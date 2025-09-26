import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';


const cameraScale = 1.2;

export interface StlGeometry {
  left: number,
  right: number,
  bottom: number,
  top: number,
  front: number,
  back: number,
  width: number,
  height: number,
  depth: number,
  mid_x: number,
  mid_y: number,
  mid_z: number,
}

export class Viewer {
  scene: THREE.Scene;
  geometry: THREE.BufferGeometry;
  loader: STLLoader;
  renderer: THREE.WebGLRenderer;
  material: THREE.Material;
  mesh: THREE.Mesh;

  camera: THREE.Camera;
  cameraTarget: THREE.Vector3;
  controls: OrbitControls;
  light: THREE.DirectionalLight;
  lightTarget: THREE.Object3D;
  ambientLight: THREE.AmbientLight;
  stlSize: number;
  stlGeo: StlGeometry;

  constructor(el: HTMLElement) {
    this.loader = new STLLoader();

    const rect = el.getBoundingClientRect();
    this.renderer = new THREE.WebGLRenderer();
    this.renderer.setSize(rect.width, rect.height);
    el.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1e2124);
    const axesHelper = new THREE.AxesHelper(5);
    // scene.add(axesHelper);

    this.light = new THREE.DirectionalLight(0xffffff, 2);
    this.scene.add(this.light);
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    this.scene.add(this.ambientLight);

    this.camera = new THREE.PerspectiveCamera(75, rect.width / rect.height, 0.1, 1000);
    this.camera.add(axesHelper);
    axesHelper.position.set(0.5, -0.5, -1);
    axesHelper.rotation.set(0, 0, 0);


    this.geometry = new THREE.BoxGeometry(1, 1, 1);
    // const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
    // this.material = new THREE.MeshStandardMaterial({color: 0xffa500})
    this.material = new THREE.MeshPhysicalMaterial({ color: 0xffa500 });

    this.mesh = new THREE.Mesh(this.geometry, this.material);
    this.scene.add(this.mesh);

    this.camera.position.y = 2;
    this.lightTarget = new THREE.Object3D();
    this.scene.add(this.lightTarget)
    this.cameraTarget = new THREE.Vector3(0, - 0.25, 0);
    this.stlGeo = {
      left: 0, right: 1, top: 1, bottom: 0, front: 1, back: 0,
      width: 1, height: 1, depth: 1, mid_x: 0.5, mid_y: 0.5, mid_z: 0.5
    }
    
    this.controls = new OrbitControls(this.camera, el);
    this.controls.enablePan = false;
    this.controls.target = this.cameraTarget;
    this.controls.autoRotate = true;
    this.controls.update();

    el.addEventListener('click', e => {
      console.log('rotate:', this.controls.autoRotate)
      if (this.controls.autoRotate) {
        this.controls.autoRotate = false;
        this.controls.update();
      }
    })

    const animate = () => {
      this.animate();
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    }
    this.renderer.setAnimationLoop(animate);
  }

  load(stl: string, geo: StlGeometry) {
    this.scene.remove(this.mesh);
    this.geometry.dispose();

    this.stlGeo = geo;
    // I hate this method but I spent way too long trying to figure this out
    const bytes = base64toUint8(stl);
    this.geometry = this.loader.parse(bytes.buffer);
    this.mesh = new THREE.Mesh(this.geometry, this.material);
    this.scene.add(this.mesh);
    this.resetCamera();
  }

  resetCamera() {
    this.camera.position.y = this.stlGeo.height * 2 - this.stlGeo.bottom;
    this.stlSize = Math.max(this.stlGeo.width, this.stlGeo.height, this.stlGeo.depth);
    this.stlGeo = this.stlGeo;
    this.cameraTarget.x = this.stlGeo.mid_x;
    this.cameraTarget.y = this.stlGeo.mid_y;
    this.cameraTarget.z = this.stlGeo.mid_z;
    this.lightTarget.position.set(this.cameraTarget.x, this.cameraTarget.y, this.cameraTarget.z);
    this.controls.autoRotate = true;
    this.controls.update();
  }

  animate() {
    this.camera.lookAt(this.cameraTarget);
    this.light.position.x = this.camera.position.x;
    this.light.position.y = this.camera.position.y;
    this.light.position.z = this.camera.position.z;
  }
}


export function base64toUint8(b64: string) {
  const binaryString = atob(b64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}
