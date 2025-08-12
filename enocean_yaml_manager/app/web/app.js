// UI : CRUD + import/export + EEP + affichage conditionnel par type
const $ = (sel) => document.querySelector(sel);
const devicesDiv = $("#devices");
const channelsDiv = $("#channels");
const form = $("#device-form");
const opResult = $("#op-result");
const eHaType = $("#ha_type");
const eEep = $("#eep");

// Base Ingress : on calcule le "chemin racine" à partir de l'URL courante.
// Ex: /api/hassio_ingress/<token>/ -> BASE="/api/hassio_ingress/<token>"
const BASE = window.location.pathname.replace(/\/$/, "");
const api = (path, opts={}) => fetch(`${BASE}${path}`, opts);

// Affiche les chemins (indicatif)
$("#auto-path").textContent = "/config/packages/enocean_auto.yaml";
$("#cfg-path").textContent = "/config/packages/enocean_yaml_config.yaml";

// --- Affichage conditionnel des sections selon ha_type ---
const panelSwitch = $("#panel-switch");
const panelLight  = $("#panel-light");
const panelSensor = $("#panel-sensor");

function updateVisibility() {
  const t = eHaType.value;
  panelSwitch.open = t === "switch";
  panelLight.open  = t === "light";
  panelSensor.open = t === "sensor";
  panelSwitch.style.display = (t === "switch") ? "" : "none";
  panelLight.style.display  = (t === "light") ? "" : "none";
  panelSensor.style.display = (t === "sensor") ? "" : "none";
}
eHaType.addEventListener("change", updateVisibility);
updateVisibility();

// --- EEP : charger la liste et remplir le select ---
async function loadEEPs() {
  const res = await api("/api/eep");
  const json = await res.json();
  eEep.innerHTML = `<option value="">(aucun)</option>`;
  (json.profiles || []).forEach(p => {
    const label = p.title ? `${p.eep} — ${p.title}` : p.eep;
    const range = (p.channel_min!=null && p.channel_max!=null) ? ` [${p.channel_min}..${p.channel_max}]` : "";
    const opt = document.createElement("option");
    opt.value = p.eep;
    opt.textContent = label + range;
    eEep.appendChild(opt);
  });
}
loadEEPs();

// --- Éditeur de canaux ---
function channelRow(idx) {
  // Ligne d’édition d’un canal + émetteur
  const row = document.createElement("div");
  row.className = "channel-row";
  row.innerHTML = `
    <label>Canal <input name="channels.${idx}.channel" type="number" value="${idx}"/></label>
    <label>Label <input name="channels.${idx}.label" value="Canal ${idx}"/></label>
    <label>Émetteur ID <input name="channels.${idx}.emitter.id" placeholder="(optionnel)"/></label>
    <label>Émetteur type
      <select name="channels.${idx}.emitter.kind">
        <option value="">(aucun)</option>
        <option value="binary_sensor">binary_sensor</option>
        <option value="switch">switch</option>
      </select>
    </label>
    <label>Émetteur label <input name="channels.${idx}.emitter.label" placeholder="(optionnel)"/></label>
    <button type="button" class="rm">🗑</button>
  `;
  row.querySelector(".rm").onclick = () => row.remove();
  return row;
}

$("#add-channel").onclick = () => {
  const idx = channelsDiv.childElementCount;
  channelsDiv.appendChild(channelRow(idx));
};

// --- Génération de canaux depuis l'EEP sélectionné ---
$("#gen-channels").onclick = async () => {
  const eep = eEep.value;
  if (!eep) {
    alert("Sélectionnez un EEP d'abord.");
    return;
  }
  const r = await api(`/api/suggest/channels?eep=${encodeURIComponent(eep)}`);
  const json = await r.json();
  const chans = json.channels || [];
  if (!chans.length) {
    alert("Aucun canal suggéré pour cet EEP.");
    return;
  }
  channelsDiv.innerHTML = "";
  chans.forEach((c, i) => {
    const row = channelRow(i);
    row.querySelector(`[name="channels.${i}.channel"]`).value = c;
    row.querySelector(`[name="channels.${i}.label"]`).value = `Canal ${c}`;
    channelsDiv.appendChild(row);
  });
};

// --- Form helpers ---
function formToObj(formEl) {
  // Transforme le formulaire en un objet Device (cf. models.py)
  const data = new FormData(formEl);
  const obj = { channels: [], sensor_options: {}, light_sender: {} };
  for (const [k,v] of data.entries()) {
    if (k.startsWith("channels.")) {
      const [, idx, ...rest] = k.split(".");
      const key = rest.join(".");
      obj.channels[+idx] = obj.channels[+idx] || {channel:0,label:""};
      if (key === "channel") obj.channels[+idx].channel = Number(v);
      else if (key === "label") obj.channels[+idx].label = v;
      else if (key === "emitter.id") {
        obj.channels[+idx].emitter = obj.channels[+idx].emitter || {};
        obj.channels[+idx].emitter.id = v;
      } else if (key === "emitter.kind") {
        obj.channels[+idx].emitter = obj.channels[+idx].emitter || {};
        obj.channels[+idx].emitter.kind = v || undefined;
      } else if (key === "emitter.label") {
        obj.channels[+idx].emitter = obj.channels[+idx].emitter || {};
        obj.channels[+idx].emitter.label = v || undefined;
      }
    } else if (k.startsWith("sensor_options.")) {
      const key = k.split(".")[1];
      obj.sensor_options[key] = ["min_temp","max_temp","range_from","range_to"].includes(key) ? Number(v) : v;
    } else if (k.startsWith("light_sender.")) {
      obj.light_sender[k.split(".")[1]] = v;
    } else {
      obj[k] = v;
    }
  }
  if (!obj.sensor_options.device_class) delete obj.sensor_options;
  if (!obj.light_sender.sender_id) delete obj.light_sender;
  obj.channels = (obj.channels || []).filter(Boolean);
  obj.id_hex = (obj.id_hex || "").toUpperCase();
  obj.eep = (obj.eep || "") || undefined;
  return obj;
}

// --- CRUD & Import/Export ---
async function refresh() {
  const res = await api("/api/devices");
  const json = await res.json();
  const items = Object.entries(json.devices || {});
  devicesDiv.innerHTML = "";
  if (!items.length) {
    devicesDiv.textContent = "(aucun appareil)";
    return;
  }
  items.forEach(([key, dev]) => {
    const d = document.createElement("div");
    d.className = "dev";
    d.innerHTML = `
      <div><b>${dev.label}</b> — ${dev.ha_type} — EEP: ${dev.eep||"—"} — ID/clé: <code>${key}</code></div>
      ${dev.ha_type==="switch" ? `<div>Canaux: ${(dev.channels||[]).map(c=>`${c.channel} (${c.label})`).join(", ")||"—"}</div>` : ""}
      ${dev.ha_type==="light" ? `<div>sender_id: ${dev.light_sender?.sender_id||"—"}</div>` : ""}
      ${dev.ha_type==="sensor" ? `<div>device_class: ${dev.sensor_options?.device_class||"—"}</div>` : ""}
      <div class="actions">
        <button data-id="${key}" class="edit">✏️</button>
        <button data-id="${key}" class="del">🗑</button>
      </div>
    `;
    d.querySelector(".del").onclick = async (e) => {
      const id = e.target.dataset.id;
      await api(`/api/devices/${encodeURIComponent(id)}`, { method: "DELETE" });
      refresh();
    };
    d.querySelector(".edit").onclick = async (e) => {
      const id = e.target.dataset.id;
      const r = await api(`/api/devices/${encodeURIComponent(id)}`);
      if (!r.ok) return;
      const dev = await r.json();
      form.reset();
      form.id_hex.value = dev.id_hex || "";
      form.label.value = dev.label || "";
      eHaType.value = dev.ha_type || "switch";
      updateVisibility();
      eEep.value = dev.eep || "";
      channelsDiv.innerHTML = "";
      (dev.channels||[]).forEach((c, i) => {
        const row = channelRow(i);
        row.querySelector(`[name="channels.${i}.channel"]`).value = c.channel ?? 0;
        row.querySelector(`[name="channels.${i}.label"]`).value = c.label || "";
        if (c.emitter) {
          row.querySelector(`[name="channels.${i}.emitter.id"]`).value = c.emitter.id || "";
          row.querySelector(`[name="channels.${i}.emitter.kind"]`).value = c.emitter.kind || "";
          row.querySelector(`[name="channels.${i}.emitter.label"]`).value = c.emitter.label || "";
        }
        channelsDiv.appendChild(row);
      });
      if (dev.light_sender?.sender_id) {
        form.querySelector(`[name="light_sender.sender_id"]`).value = dev.light_sender.sender_id;
      }
      if (dev.sensor_options?.device_class) {
        form.querySelector(`[name="sensor_options.device_class"]`).value = dev.sensor_options.device_class;
        ["min_temp","max_temp","range_from","range_to"].forEach(k=>{
          const el = form.querySelector(`[name="sensor_options.${k}"]`);
          if (el && dev.sensor_options[k] !== undefined) el.value = dev.sensor_options[k];
        });
      }
      window.scrollTo({top:0,behavior:"smooth"});
    };
    devicesDiv.appendChild(d);
  });
}

form.onsubmit = async (e) => {
  e.preventDefault();
  const payload = formToObj(form);
  const res = await api("/api/devices", {
    method: "POST",
    headers: {"content-type":"application/json"},
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    await refresh();
    alert("Appareil enregistré");
  } else {
    alert("Erreur d’enregistrement");
  }
};

$("#export").onclick = async () => {
  opResult.textContent = "Export en cours...";
  const res = await api("/api/export", { method:"POST" });
  const json = await res.json();
  if (json.ok) {
    opResult.textContent = `Écrit: ${json.auto_output} et ${json.config_output}`;
  } else {
    opResult.textContent = "Erreur export";
  }
};

$("#import").onclick = async () => {
  opResult.textContent = "Import en cours...";
  const res = await api("/api/import", { method:"POST" });
  const json = await res.json();
  if (json.ok) {
    await refresh();
    opResult.textContent = `Import OK (${json.imported} appareils)`;
  } else {
    opResult.textContent = "Erreur import";
  }
};

refresh();
