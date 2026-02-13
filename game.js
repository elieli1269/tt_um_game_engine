import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.module.js';

const canvas = document.getElementById('gameCanvas');
const hpEl = document.getElementById('hp');
const scoreEl = document.getElementById('score');
const playersEl = document.getElementById('players');

const MIN_TOTAL_COMBATANTS = 8;
const BOT_FIRE_INTERVAL = 1.2;
const PLAYER_FIRE_COOLDOWN = 0.09;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x060a12, 20, 110);

const camera = new THREE.PerspectiveCamera(75, innerWidth / innerHeight, 0.1, 300);
camera.position.set(0, 1.7, 16);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;

scene.add(new THREE.HemisphereLight(0xd9e7ff, 0x1f1b16, 0.92));
const sun = new THREE.DirectionalLight(0xe7eeff, 1.45);
sun.position.set(14, 24, 8);
sun.castShadow = true;
scene.add(sun);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(240, 240),
  new THREE.MeshStandardMaterial({ color: 0x262c35, roughness: 0.88, metalness: 0.04 })
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

const blockers = [];
for (let i = 0; i < 24; i += 1) {
  const b = new THREE.Mesh(
    new THREE.BoxGeometry(4 + Math.random() * 6, 5 + Math.random() * 18, 4 + Math.random() * 6),
    new THREE.MeshStandardMaterial({ color: 0x4e5563, roughness: 0.95 })
  );
  b.position.set((Math.random() - 0.5) * 130, b.geometry.parameters.height / 2, (Math.random() - 0.5) * 130);
  b.castShadow = true;
  b.receiveShadow = true;
  blockers.push(b);
  scene.add(b);
}

const player = {
  hp: 100,
  score: 0,
  speed: 18,
  yaw: 0,
  pitch: 0,
  firing: false,
  shotCooldown: 0,
  damageFlash: 0,
};

const keys = new Set();
const bots = [];
let netPlayers = 1;
let ws;

function createBot() {
  const root = new THREE.Group();
  const torso = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.45, 0.7, 4, 8),
    new THREE.MeshStandardMaterial({ color: 0x2c66d8, roughness: 0.5 })
  );
  torso.castShadow = true;
  root.add(torso);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.27, 16, 16), new THREE.MeshStandardMaterial({ color: 0xf0c4a0 }));
  head.position.y = 0.86;
  head.castShadow = true;
  root.add(head);

  const rifle = new THREE.Mesh(
    new THREE.BoxGeometry(0.75, 0.12, 0.12),
    new THREE.MeshStandardMaterial({ color: 0x202428, metalness: 0.4, roughness: 0.4 })
  );
  rifle.position.set(0.45, 0.2, 0);
  rifle.rotation.z = 0.2;
  root.add(rifle);

  const bot = {
    root,
    hp: 100,
    cooldown: Math.random() * BOT_FIRE_INTERVAL,
    speed: 7 + Math.random() * 3,
    swing: Math.random() * Math.PI * 2,
    vel: new THREE.Vector3(),
  };

  const p = findSpawn();
  root.position.copy(p);
  root.position.y = 1.1;
  scene.add(root);
  return bot;
}

function findSpawn() {
  for (let i = 0; i < 40; i += 1) {
    const x = (Math.random() - 0.5) * 120;
    const z = (Math.random() - 0.5) * 120;
    if (blockers.every((b) => b.position.distanceToSquared(new THREE.Vector3(x, b.position.y, z)) > 36)) {
      return new THREE.Vector3(x, 0, z);
    }
  }
  return new THREE.Vector3(0, 0, 0);
}

function maintainCombatantCount() {
  const desiredBots = Math.max(0, MIN_TOTAL_COMBATANTS - netPlayers);
  while (bots.length < desiredBots) bots.push(createBot());
  while (bots.length > desiredBots) {
    const dead = bots.pop();
    scene.remove(dead.root);
  }
  playersEl.textContent = `Joueurs ${netPlayers + bots.length}`;
}

function connectPresenceSocket() {
  const wsParam = new URLSearchParams(location.search).get('ws');
  if (!wsParam) {
    maintainCombatantCount();
    return;
  }
  ws = new WebSocket(wsParam);
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'presence' && Number.isFinite(msg.players)) {
        // Allow 0 human players from backend presence to force full-bot filling.
        netPlayers = Math.max(0, Math.floor(msg.players));
        maintainCombatantCount();
      }
    } catch {
      // silence invalid payloads
    }
  };
  ws.onopen = maintainCombatantCount;
  ws.onerror = maintainCombatantCount;
  ws.onclose = () => {
    // Fallback to local-only assumption when the presence channel drops.
    netPlayers = 1;
    maintainCombatantCount();
  };
}

const raycaster = new THREE.Raycaster();
function firePlayerShot() {
  raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
  const meshes = bots.map((b) => b.root);
  const hit = raycaster.intersectObjects(meshes, true)[0];
  if (!hit) return;
  const bot = bots.find((b) => b.root === hit.object || b.root.children.includes(hit.object));
  if (!bot) return;

  bot.hp -= 34;
  if (bot.hp <= 0) {
    player.score += 1;
    scoreEl.textContent = `Score ${player.score}`;
    bot.hp = 100;
    bot.root.position.copy(findSpawn()).setY(1.1);
  }
}

function handleInput(dt) {
  const forward = new THREE.Vector3(Math.sin(player.yaw), 0, Math.cos(player.yaw) * -1);
  const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
  const move = new THREE.Vector3();
  if (keys.has('KeyW')) move.add(forward);
  if (keys.has('KeyS')) move.sub(forward);
  if (keys.has('KeyA')) move.sub(right);
  if (keys.has('KeyD')) move.add(right);
  if (move.lengthSq()) {
    move.normalize().multiplyScalar(player.speed * dt);
    camera.position.add(move);
  }
  camera.position.x = THREE.MathUtils.clamp(camera.position.x, -118, 118);
  camera.position.z = THREE.MathUtils.clamp(camera.position.z, -118, 118);
}

function updateBots(dt) {
  const playerPos = camera.position;
  bots.forEach((bot) => {
    const toPlayer = new THREE.Vector3().subVectors(playerPos, bot.root.position);
    const dist = toPlayer.length();
    toPlayer.normalize();

    bot.swing += dt * 7;
    bot.root.lookAt(playerPos.x, bot.root.position.y + 0.4, playerPos.z);
    bot.root.position.addScaledVector(toPlayer, dt * bot.speed * (dist > 10 ? 1 : -0.35));
    bot.root.position.y = 1.1 + Math.sin(bot.swing) * 0.03;

    bot.cooldown -= dt;
    if (bot.cooldown <= 0 && dist < 46) {
      bot.cooldown = BOT_FIRE_INTERVAL + Math.random() * 0.45;
      if (Math.random() < 0.55) {
        player.hp = Math.max(0, player.hp - 5);
        player.damageFlash = 0.18;
        hpEl.textContent = `HP ${player.hp}`;
      }
    }
  });

  if (player.hp <= 0) {
    player.hp = 100;
    hpEl.textContent = 'HP 100';
    camera.position.copy(findSpawn()).setY(1.7);
  }
}

function animate() {
  const dt = Math.min(0.05, clock.getDelta());
  handleInput(dt);
  updateBots(dt);

  if (player.firing) {
    player.shotCooldown -= dt;
    if (player.shotCooldown <= 0) {
      player.shotCooldown = PLAYER_FIRE_COOLDOWN;
      firePlayerShot();
    }
  } else {
    player.shotCooldown = 0;
  }

  player.damageFlash = Math.max(0, player.damageFlash - dt);
  renderer.setClearColor(player.damageFlash > 0 ? 0x3a0b0b : 0x050911);
  camera.rotation.set(player.pitch, player.yaw, 0, 'YXZ');
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

const clock = new THREE.Clock();
window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

window.addEventListener('keydown', (e) => keys.add(e.code));
window.addEventListener('keyup', (e) => keys.delete(e.code));
window.addEventListener('mousedown', (e) => {
  if (e.button === 0) player.firing = true;
});
window.addEventListener('mouseup', (e) => {
  if (e.button === 0) player.firing = false;
});
window.addEventListener('mousemove', (e) => {
  if (document.pointerLockElement !== canvas) return;
  player.yaw -= e.movementX * 0.0022;
  player.pitch -= e.movementY * 0.0022;
  player.pitch = THREE.MathUtils.clamp(player.pitch, -1.25, 1.25);
});


function requestPointerLockSafely() {
  if (document.pointerLockElement === canvas) return;
  canvas.requestPointerLock().catch(() => {
    // Some browsers require explicit user interaction; fallback listeners below handle it.
  });
}

// Best effort: show scene immediately and try pointer lock as soon as possible.
setTimeout(requestPointerLockSafely, 0);
window.addEventListener('pointerdown', requestPointerLockSafely, { once: true });
window.addEventListener('keydown', requestPointerLockSafely, { once: true });

connectPresenceSocket();
animate();
