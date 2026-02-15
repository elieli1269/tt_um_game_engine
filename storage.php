<?php

declare(strict_types=1);

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/crypto_lib.php';

function ensure_storage(): void
{
    if (!is_dir(DATA_DIR)) {
        mkdir(DATA_DIR, 0775, true);
    }
    if (!is_file(MESSAGES_FILE)) {
        file_put_contents(MESSAGES_FILE, "[]\n");
    }
    if (!is_dir(USER_COPY_DIR)) {
        mkdir(USER_COPY_DIR, 0775, true);
    }

    foreach (array_keys(USERS) as $user) {
        $userDir = USER_COPY_DIR . '/' . $user;
        if (!is_dir($userDir)) {
            mkdir($userDir, 0775, true);
        }
        $file = $userDir . '/messages.json';
        if (!is_file($file)) {
            file_put_contents($file, "[]\n");
        }
    }
}

function load_messages(): array
{
    ensure_storage();
    $raw = file_get_contents(MESSAGES_FILE);
    $data = json_decode($raw ?: '[]', true);

    return is_array($data) ? $data : [];
}

function save_messages(array $messages): void
{
    file_put_contents(MESSAGES_FILE, json_encode($messages, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

function append_user_copy(string $user, array $message): void
{
    $file = USER_COPY_DIR . '/' . $user . '/messages.json';
    $raw = file_get_contents($file);
    $items = json_decode($raw ?: '[]', true);
    if (!is_array($items)) {
        $items = [];
    }

    $items[] = [
        'id' => $message['id'],
        'sender' => $message['sender'],
        'kind' => $message['kind'],
        'target' => $message['target'],
        'ciphertext' => $message['ciphertext'],
        'created_at' => $message['created_at'],
        'stored_for_user' => $user,
    ];

    file_put_contents($file, json_encode($items, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

function get_recipients(array $message): array
{
    if ($message['kind'] === 'group') {
        return GROUPS[$message['target']] ?? [];
    }

    return [$message['target']];
}

function build_message(string $sender, string $kind, string $target, string $plainText, bool $external = false): array
{
    $messages = load_messages();
    $nextId = empty($messages) ? 1 : ((int) end($messages)['id'] + 1);

    $cipherByRecipient = [];
    foreach (get_recipients(['kind' => $kind, 'target' => $target]) as $recipient) {
        $cipherByRecipient[$recipient] = encrypt_text($plainText, USERS[$recipient]);
    }

    return [
        'id' => $nextId,
        'sender' => $sender,
        'kind' => $kind,
        'target' => $target,
        'external' => $external,
        'cipher_by_recipient' => $cipherByRecipient,
        'ciphertext' => encrypt_text($plainText, USERS[get_recipients(['kind' => $kind, 'target' => $target])[0]]),
        'created_at' => gmdate('c'),
    ];
}

function persist_message(array $message, bool $mirror = true): void
{
    $messages = load_messages();
    $messages[] = $message;
    save_messages($messages);

    foreach (array_keys($message['cipher_by_recipient']) as $recipient) {
        $copy = $message;
        $copy['ciphertext'] = $message['cipher_by_recipient'][$recipient];
        append_user_copy($recipient, $copy);
    }

    if ($mirror) {
        mirror_to_remote($message);
    }
}

function mirror_to_remote(array $message): void
{
    if (!defined('REMOTE_MIRROR_URL') || REMOTE_MIRROR_URL === '') {
        return;
    }

    $payload = json_encode([
        'token' => API_MIRROR_TOKEN,
        'message' => $message,
    ]);

    if (!function_exists('curl_init')) {
        return;
    }

    $ch = curl_init(REMOTE_MIRROR_URL);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 2,
        CURLOPT_TIMEOUT => 3,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS => $payload,
    ]);

    curl_exec($ch);
    curl_close($ch);
}

function decrypt_for_user(array $message, string $user): array
{
    $cipher = $message['cipher_by_recipient'][$user] ?? null;
    if ($cipher === null) {
        return [];
    }

    $plain = decrypt_text($cipher, USERS[$user]);

    return [
        'id' => $message['id'],
        'sender' => $message['sender'],
        'kind' => $message['kind'],
        'target' => $message['target'],
        'external' => $message['external'],
        'message' => $plain,
        'created_at' => $message['created_at'],
    ];
}
