import * as THREE from 'three/webgpu';
import poses from './data/camera-poses.json';

export interface Pose {
  /** metres */
  position: [number, number, number];
  /** degrees; 0 looks down -Z, positive turns left */
  yaw: number;
  /** degrees; positive looks up */
  pitch: number;
  /** horizontal field of view, degrees */
  hfov: number;
}

export const poseTable = poses as unknown as Record<string, Pose>;

export function applyPose(camera: THREE.PerspectiveCamera, name: string): boolean {
  const p = poseTable[name];
  if (!p) return false;
  camera.position.set(...p.position);
  camera.rotation.set(THREE.MathUtils.degToRad(p.pitch), THREE.MathUtils.degToRad(p.yaw), 0, 'YXZ');
  const h = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(p.hfov) / 2) / camera.aspect);
  camera.fov = THREE.MathUtils.radToDeg(h);
  camera.updateProjectionMatrix();
  return true;
}
