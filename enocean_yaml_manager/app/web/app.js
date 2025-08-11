// JS minimal pour la petite UI : CRUD + import/export
const $ = (sel) => document.querySelector(sel);
const devicesDiv = $("#devices");
const channelsDiv = $("#channels");
const form = $("#device-form");
const opResult = $("#op-result");

// Affiche les chemins (par défaut, identiques à run.sh)
$("#auto-path").textContent = "/config/packages/enocean_auto.yaml";
$("#cfg-path").textContent = "/config/packages/enocean_yaml_config.yaml";

function channelRow(idx) {
  // Ligne d’édition d’un canal + infos émetteur
  const row = document.createElement("div");
  row.className = "channel-row";
  row.innerHTML = `
    <label>Canal <input name="channels.${idx}.channel" type="number" value="${idx}"/></label>
    <label>Label <input name="channels.${idx}.label" value="Canal ${idx}"/></label>
    <label>Émetteur ID <input name="channels.${idx}.emitter_id" placeholder="(optionnel)"/></label>
    <label>Émetteur type
      <select name="channels.${idx}.emitter_kind">
        <option value="">(aucun)</option>
        <option value="binary_sensor">binary_sensor</option>
        <option value="switch">switch</option>
      </select>
    </label>
    <label>Émetteur label <input name="channels.${idx}.emitter_label" placeholder="(optionnel)"/></label>
    <button type="button" class="rm">🗑</button>
  `;
  row.querySelector(".rm").onclick = () => row.remove();
  return row;
}

$("#add-channel").onclick = () => {
  const idx = channelsDiv.childElementCount;
  channelsDiv.appendChild(channelRow(idx));
};

function formToObj(formEl) {
  // Transforme le formulaire en objet Device (cf. models.py)
  const data = new FormData(formEl);
  const obj = { channels: [], sensor_options: {}, light_sender: {} };
  for (const [k,v] of data.entries()) {
    if (k.startsWith("channels.")) {
      const [, idx, key] = k.split(".");
      obj.channels[+idx] = obj.channels[+idx] || {channel:0,label:""};
      obj.channels[+idx][key] = key === "channel" ? Number(v) : v;
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
  obj.id_hex = (obj.id_hex || "").toUpperCase(); // normalise l’ID
  return obj;
}

async function refresh() {
  // Recharge la liste d’appareils depuis l’API
  const res = await fetch("/api/devices");
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
      <div><b>${dev.label}</b> — ${dev.ha_type} — ID/clé: <code>${key}</code></div>
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
      await fetch(`/api/devices/${encodeURIComponent(id)}`, { method: "DELETE" });
      refresh();
    };
    d.querySelector(".edit").onclick = async (e) => {
      const id = e.target.dataset.id;
      const r = await fetch(`/api/devices/${encodeURIComponent(id)}`);
      if (!r.ok) return;
      const dev = await r.json();
      form.reset();
      form.id_hex.value = dev.id_hex || "";
      form.label.value = dev.label || "";
      form.ha_type.value = dev.ha_type || "switch";
      channelsDiv.innerHTML = "";
      (dev.channels||[]).forEach((c, i) => {
        const row = channelRow(i);
        row.querySelector(`[name="channels.${i}.channel"]`).value = c.channel ?? 0;
        row.querySelector(`[name="channels.${i}.label"]`).value = c.label || "";
        row.querySelector(`[name="channels.${i}.emitter_id"]`).value = c.emitter_id || "";
        row.querySelector(`[name="channels.${i}.emitter_kind"]`).value = c.emitter_kind || "";
        row.querySelector(`[name="channels.${i}.emitter_label"]`).value = c.emitter_label || "";
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
  // Enregistrement d’un appareil
  e.preventDefault();
  const payload = formToObj(form);
  const res = await fetch("/api/devices", {
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
  // Écrit les 2 YAML
  opResult.textContent = "Export en cours...";
  const res = await fetch("/api/export", { method:"POST" });
  const json = await res.json();
  if (json.ok) {
    opResult.textContent = `Écrit: ${json.auto_output} et ${json.config_output}`;
  } else {
    opResult.textContent = "Erreur export";
  }
};

$("#import").onclick = async () => {
  // Lit les 2 YAML puis recharge le registre
  opResult.textContent = "Import en cours...";
  const res = await fetch("/api/import", { method:"POST" });
  const json = await res.json();
  if (json.ok) {
    await refresh();
    opResult.textContent = `Import OK (${json.imported} appareils)`;
  } else {
    opResult.textContent = "Erreur import";
  }
};

refresh();
