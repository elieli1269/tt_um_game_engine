<?php

declare(strict_types=1);

require_once __DIR__ . '/storage.php';

header('Content-Type: application/json; charset=utf-8');

function json_body(): array
{
    $raw = file_get_contents('php://input');
    $data = json_decode($raw ?: '{}', true);
    return is_array($data) ? $data : [];
}

function respond(array $payload, int $status = 200): void
{
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit;
}

$action = $_GET['action'] ?? '';

if ($action === 'users') {
    respond(['users' => array_keys(USERS), 'groups' => GROUPS]);
}

if ($action === 'send') {
    $body = json_body();
    $sender = strtolower(trim((string) ($body['sender'] ?? '')));
    $kind = strtolower(trim((string) ($body['kind'] ?? 'user')));
    $target = strtolower(trim((string) ($body['target'] ?? '')));
    $text = trim((string) ($body['message'] ?? ''));
    $external = (bool) ($body['external'] ?? false);

    if (!isset(USERS[$sender])) {
        respond(['error' => 'Expéditeur inconnu'], 400);
    }
    if ($text === '') {
        respond(['error' => 'Message vide'], 400);
    }

    if ($kind === 'user' && !isset(USERS[$target])) {
        respond(['error' => 'Destinataire inconnu'], 400);
    }

    if ($kind === 'group' && !isset(GROUPS[$target])) {
        respond(['error' => 'Groupe inconnu'], 400);
    }

    $msg = build_message($sender, $kind, $target, $text, $external);
    persist_message($msg, true);
    respond(['status' => 'ok', 'id' => $msg['id']]);
}

if ($action === 'inbox') {
    $user = strtolower(trim((string) ($_GET['user'] ?? '')));
    $mode = strtolower(trim((string) ($_GET['mode'] ?? 'decrypted')));
    $afterId = (int) ($_GET['after_id'] ?? 0);

    if (!isset(USERS[$user])) {
        respond(['error' => 'Utilisateur inconnu'], 404);
    }

    $messages = load_messages();
    $out = [];

    foreach ($messages as $message) {
        if ((int) $message['id'] <= $afterId) {
            continue;
        }

        if (!isset($message['cipher_by_recipient'][$user])) {
            continue;
        }

        if ($mode === 'encrypted') {
            $out[] = [
                'id' => $message['id'],
                'sender' => $message['sender'],
                'kind' => $message['kind'],
                'target' => $message['target'],
                'external' => $message['external'],
                'ciphertext' => $message['cipher_by_recipient'][$user],
                'created_at' => $message['created_at'],
            ];
            continue;
        }

        $out[] = decrypt_for_user($message, $user);
    }

    respond(['messages' => $out]);
}

if ($action === 'call_link') {
    $room = preg_replace('/[^a-zA-Z0-9_-]/', '', (string) ($_GET['room'] ?? 'global-room'));
    $video = ((string) ($_GET['video'] ?? '0')) === '1';
    $base = 'https://meet.jit.si/' . $room;
    $link = $video ? $base : $base . '#config.startWithVideoMuted=true';
    respond(['url' => $link]);
}

respond(['error' => 'Action inconnue'], 404);
