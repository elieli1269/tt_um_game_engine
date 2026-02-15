<?php

declare(strict_types=1);

const APP_NAME = 'Messagerie sécurisée hybride';
const API_MIRROR_TOKEN = 'change_me_mirror_token';

const USERS = [
    'luc' => 'luc_demo_key_2026',
    'alice' => 'alice_demo_key_2026',
    'bob' => 'bob_demo_key_2026',
    'eva' => 'eva_demo_key_2026',
];

const GROUPS = [
    'famille' => ['luc', 'alice', 'bob'],
    'projet' => ['luc', 'eva', 'alice'],
];

const DATA_DIR = __DIR__ . '/data';
const MESSAGES_FILE = DATA_DIR . '/messages.json';
const USER_COPY_DIR = DATA_DIR . '/user_copies';

// Le miroir distant peut pointer vers: https://eliphotos.alwaysdata.net/messaging/mirror.php
const REMOTE_MIRROR_URL = 'https://eliphotos.alwaysdata.net/messaging/mirror.php';
