<?php

declare(strict_types=1);

function derive_key(string $secret): string
{
    return hash('sha256', $secret, true);
}

function keystream(string $key, string $nonce, int $length): string
{
    $out = '';
    $counter = 0;
    while (strlen($out) < $length) {
        $counterBytes = pack('N2', ($counter >> 32) & 0xFFFFFFFF, $counter & 0xFFFFFFFF);
        $block = hash_hmac('sha256', $nonce . $counterBytes, $key, true);
        $out .= $block;
        $counter++;
    }

    return substr($out, 0, $length);
}

function xor_bytes(string $a, string $b): string
{
    $len = strlen($a);
    $out = '';
    for ($i = 0; $i < $len; $i++) {
        $out .= $a[$i] ^ $b[$i];
    }

    return $out;
}

function encrypt_text(string $plaintext, string $secret): string
{
    $key = derive_key($secret);
    $nonce = random_bytes(16);
    $stream = keystream($key, $nonce, strlen($plaintext));
    $cipher = xor_bytes($plaintext, $stream);
    $tag = hash_hmac('sha256', $nonce . $cipher, $key, true);
    $payload = $nonce . $cipher . $tag;

    return strtr(base64_encode($payload), '+/', '-_');
}

function decrypt_text(string $token, string $secret): string
{
    $key = derive_key($secret);
    $padded = strtr($token, '-_', '+/');
    $padded .= str_repeat('=', (4 - strlen($padded) % 4) % 4);

    $data = base64_decode($padded, true);
    if ($data === false || strlen($data) < 48) {
        throw new RuntimeException('Token invalide');
    }

    $nonce = substr($data, 0, 16);
    $rest = substr($data, 16);
    $cipher = substr($rest, 0, -32);
    $tag = substr($rest, -32);
    $expected = hash_hmac('sha256', $nonce . $cipher, $key, true);

    if (!hash_equals($expected, $tag)) {
        throw new RuntimeException('Intégrité invalide');
    }

    $stream = keystream($key, $nonce, strlen($cipher));
    return xor_bytes($cipher, $stream);
}
