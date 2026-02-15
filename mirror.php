<?php

declare(strict_types=1);

require_once __DIR__ . '/storage.php';

header('Content-Type: application/json; charset=utf-8');

$body = json_decode(file_get_contents('php://input') ?: '{}', true);
if (!is_array($body)) {
    http_response_code(400);
    echo json_encode(['error' => 'JSON invalide']);
    exit;
}

if (($body['token'] ?? '') !== API_MIRROR_TOKEN) {
    http_response_code(403);
    echo json_encode(['error' => 'Token invalide']);
    exit;
}

$message = $body['message'] ?? null;
if (!is_array($message) || !isset($message['id'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Message invalide']);
    exit;
}

persist_message($message, false);
echo json_encode(['status' => 'mirrored']);
