import * as THREE from 'three/webgpu';
import { LEVEL_COLOR, type Level } from '../hud/prompt';

/**
 * Bounding-box edge outline in the level colour. One shared LineSegments + one material:
 * identical on WebGPU and WebGL2, no extra mesh passes, no per-object material clones.
 */
export class Highlight {
  private lines: THREE.LineSegments;
  private mat = new THREE.LineBasicNodeMaterial({ color: 0xffffff, depthTest: false, transparent: true, opacity: 0.9 });
  private box = new THREE.Box3();
  private size = new THREE.Vector3();
  private lastObj: THREE.Object3D | null = null;
  private lastLevel: Level | null = null;
  private lastMat = new THREE.Matrix4();

  constructor(scene: THREE.Scene) {
    this.lines = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)), this.mat);
    this.lines.frustumCulled = false;
    this.lines.renderOrder = 999;
    this.lines.raycast = () => {};
    this.lines.scale.setScalar(0.0001); // stays "visible" so the pipeline compiles on the first frame
    scene.add(this.lines);
  }

  set(obj: THREE.Object3D | null, level: Level = 'look') {
    if (!obj) { this.lines.scale.setScalar(0.0001); this.lastObj = null; return; }
    obj.updateWorldMatrix(true, false);
    if (obj === this.lastObj && level === this.lastLevel && obj.matrixWorld.equals(this.lastMat)) return; // unchanged
    this.lastObj = obj;
    this.lastLevel = level;
    this.lastMat.copy(obj.matrixWorld);
    this.box.setFromObject(obj);
    this.box.getSize(this.size).addScalar(0.02);
    this.box.getCenter(this.lines.position);
    this.lines.scale.copy(this.size);
    this.mat.color.setHex(LEVEL_COLOR[level]);
  }
}
