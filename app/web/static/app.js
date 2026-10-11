// AI Live Director v0.1 —— Dashboard WebSocket 客户端
(function () {
  const $ = (id) => document.getElementById(id);

  const scheme = location.protocol === "https:" ? "wss://" : "ws://";
  const ws = new WebSocket(scheme + location.host + "/ws");

  // 初始化 4 个机位预览占位
  const previewsEl = $("previews");
  const camNames = ["CAM1", "CAM2", "CAM3", "CAM4"];
  const camImgs = {};
  camNames.forEach((c) => {
    const div = document.createElement("div");
    div.className = "cam";
    div.innerHTML = `<div class="cam-name">${c}</div><img alt="${c}">`;
    previewsEl.appendChild(div);
    camImgs[c] = div;
  });

  const setImg = (img, b64) => { img.src = "data:image/jpeg;base64," + b64; };

  ws.onopen = () => { $("status").textContent = "直播中…"; };
  ws.onclose = () => { $("status").textContent = "连接已断开"; };
  ws.onerror = () => { $("status").textContent = "连接出错"; };

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === "step") {
      setImg($("program"), msg.program);
      for (const [c, b64] of Object.entries(msg.previews)) {
        if (camImgs[c]) setImg(camImgs[c].querySelector("img"), b64);
      }
      // 高亮当前机位
      camNames.forEach((c) => {
        camImgs[c].classList.toggle("active", c === msg.current_camera);
      });

      const wsState = msg.world_state;
      const act = msg.action;
      $("scene").textContent = wsState.scene;
      $("speaker").textContent = wsState.active_speaker || "无";
      $("interaction").textContent = wsState.interaction ? "是" : "否";
      $("product").textContent = wsState.product_visible ? "是" : "否";
      $("action").textContent = act.action;
      $("camera").textContent = act.camera || msg.current_camera;
      $("shot").textContent = act.shot || (wsState.camera && wsState.camera.shot) || "—";
      $("reason").textContent = act.reason || "—";
      $("confidence").textContent = (act.confidence != null) ? Number(act.confidence).toFixed(2) : "—";

      if (act.action === "SWITCH_CAMERA") {
        addLog(`${Number(wsState.timestamp).toFixed(1)}s  →  ${act.camera}  ·  ${act.reason}`);
      }
    } else if (msg.type === "done") {
      $("status").textContent = "本轮结束，即将重播…";
    }
  };

  function addLog(text) {
    const log = $("log");
    const li = document.createElement("li");
    li.textContent = text;
    log.prepend(li);
    while (log.children.length > 20) log.removeChild(log.lastChild);
  }
})();
