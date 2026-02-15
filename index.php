<?php
require_once __DIR__ . '/config.php';
?><!doctype html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title><?= APP_NAME ?></title>
  <link rel="stylesheet" href="static/style.css" />
</head>
<body>
  <main class="container">
    <h1><?= APP_NAME ?></h1>
    <p>Version web PHP + client Python. Messages stockés sur serveur et en copie par utilisateur.</p>

    <section class="card">
      <h2>Envoyer un message (user/groupe/externe)</h2>
      <form id="send-form">
        <label>Expéditeur <select id="sender"></select></label>
        <label>Type
          <select id="kind">
            <option value="user">Utilisateur</option>
            <option value="group">Groupe</option>
          </select>
        </label>
        <label>Cible <select id="target"></select></label>
        <label>Message <textarea id="message" rows="3" required></textarea></label>
        <label><input type="checkbox" id="external" /> Message externe</label>
        <button type="submit">Envoyer</button>
      </form>
      <p id="send-status"></p>
    </section>

    <section class="card">
      <h2>Inbox + notifications</h2>
      <label>Utilisateur <select id="inbox-user"></select></label>
      <button id="refresh-btn" type="button">Actualiser</button>
      <button id="enable-notif" type="button">Activer notifications</button>
      <ul id="messages"></ul>
    </section>

    <section class="card">
      <h2>Appel / Vision</h2>
      <label>Room <input id="room" value="groupe-famille" /></label>
      <div class="call-buttons">
        <button id="audio-call" type="button">Appel audio</button>
        <button id="video-call" type="button">Vision (vidéo)</button>
      </div>
    </section>
  </main>

  <script src="static/app.js"></script>
</body>
</html>
