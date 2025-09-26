import * as zip from "@zip.js/zip.js";

import {Editor} from './editor.js';
import {Viewer, StlGeometry, base64toUint8} from './viewer.js';

interface StlMessage  {
  data: string;
  name: string;
  volume: StlGeometry;
}

const STL_CACHE: StlMessage[] = [];
let VIEWER: Viewer;
let EDITOR: Editor;

let SELECT_EL: HTMLSelectElement;
let LOGS_EL, ATTR_EL: HTMLElement;

function findEl<T extends HTMLElement=HTMLElement>(lookup: string): T {
  const el = document.querySelector(lookup);
  if (el === null) {
    throw Error(`Failed to find element: ${lookup}`);
  }
  return el as T;
}

function removeChildren(el: HTMLElement) {
  for (const ch of Array.from(el.children)) {
    el.removeChild(ch);
  }
}

document.addEventListener('DOMContentLoaded', () => {  
  VIEWER = new Viewer(findEl('#preview'));
  SELECT_EL = findEl<HTMLSelectElement>('#stl_select');
  LOGS_EL = findEl('#log_pane ul');
  ATTR_EL = findEl('#attr_pane ul');

  // A CodeMirror compatible list of modifier keys, but with several
  // changes: run() is parameterless and key should always be lowercase
  // but with Shift added. 
  const keymap = [{
    key: 'Mod-r',
    preventDefault: true,
    run: ()  => {
      render(EDITOR.getText(), VIEWER);
      return true;
    },
  }, {
    key: 'Mod-Shift-s',
    preventDefault: true,
    run: async ()  => {
      saveAllStls();
      return true;
    },
  }, {
    key: 'Mod-s',
    preventDefault: true,
    run: async ()  => {
      saveStl();
      return true;
    },
  }]
  EDITOR = new Editor(keymap);

  SELECT_EL.addEventListener('change', async (e) => {
    const id = parseInt(SELECT_EL.value);
    const stl = STL_CACHE[id];
    if (stl === undefined) {
      const size = STL_CACHE.length-1;
      throw Error(`Failed to load from cache: id=${id}; cache: ${size}`);
    }
    VIEWER.load(stl.data, stl.volume);
  });

  findEl('#render_btn').addEventListener('click', async () => {
    await render(EDITOR.getText(), VIEWER);
  });
  for (const el of Array.from(document.querySelectorAll('.left.btn'))) {
    el.addEventListener('click', switchTab);
  }

  document.body.addEventListener('keydown', async e => {
    for (const kspec of keymap) {
      const seq = kspec.key.split('-');
      if (
        (seq.includes('Mod') === (e.ctrlKey || e.metaKey)) &&
        (seq.includes('Shift') === e.shiftKey) &&
        (seq.slice(-1)[0] == e.key.toLowerCase())
      ) {
        if (await kspec.run() && kspec.preventDefault) {
          e.preventDefault();
          return;
        }
      }
    }
  })
});

async function render(ymlSrc, viewer: Viewer) {
  removeChildren(LOGS_EL);
  const res = await fetch('/cgi-bin/render.pl', {
    method: "POST",
    body: ymlSrc,
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  STL_CACHE.length = 0;
  while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    buffer += decoder.decode(value);
    let nl = buffer.indexOf('\n');
    while (nl !== -1) {
      await processMessage(buffer.slice(0, nl), viewer);
      buffer = buffer.slice(nl+1);
      nl = buffer.indexOf('\n');
    }
  }
}

async function processMessage(line: string, viewer: Viewer) {
  let message;
  try {
    message = JSON.parse(line);
  } catch(e) {
    console.error(`Failed to decode message: ${e}`);
    console.log(line);
  }
  if ('data' in message) {
    const stl = message as StlMessage;
    if (STL_CACHE.length === 0) {
      viewer.load(stl.data, stl.volume);
      removeChildren(SELECT_EL);
    }
    const option = document.createElement('option');
    option.innerText = message['name']
    option.value = STL_CACHE.length.toString();
    SELECT_EL.appendChild(option)
    STL_CACHE.push(stl);
  } else if ('log' in message) {
    log(message.log);
  } else if ('error' in message) {
    log(message.error, 'error');
  } else {
    console.error(`Unrecognized message: ${line}`)
  }
}

function log(msg: string, cls?: string) {
    const li = document.createElement('li');
    if (cls !== undefined) {
      li.classList.add(cls);
    }
    const m = /^\[[^\]]+\]/.exec(msg);
    if (m !== null) {
      msg = msg.replace(m[0], '');
      const code = document.createElement('code');
      code.innerText = m[0];
      li.appendChild(code);
    }
    li.append(document.createTextNode(msg));
    LOGS_EL.appendChild(li);
}

function switchTab(e: Event) {
  const evtEl = e.target as HTMLElement;
  for (const el of evtEl.parentElement.children) {
    const pane = findEl((el as HTMLElement).dataset['target'])
    if (el === evtEl) {
      pane.style.display = 'block';
      el.classList.remove('secondary');
    } else {
      pane.style.display = 'none';
      el.classList.add('secondary');
    }
  }
}

function saveStl() {
  const stl = STL_CACHE[parseInt(SELECT_EL.value)];
  const blob = new Blob(
    [base64toUint8(stl.data).buffer as ArrayBuffer],
    {type: 'application/octet-stream'}
  );
  saveFile(stl.name, blob);
}

function saveFile(name: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url); // Clean up the URL object
}

async function saveAllStls() {
  const zipfile = new zip.ZipWriter(new zip.BlobWriter("application/zip"), { bufferedWrite: true });

  for (const stl of STL_CACHE) {
    await zipfile.add(stl.name, new zip.Uint8ArrayReader(base64toUint8(stl.data)));
  }
  const blob = await zipfile.close();
  saveFile('stls.zip', blob);
}
