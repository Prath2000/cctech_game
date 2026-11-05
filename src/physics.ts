import RAPIER from '@dimforge/rapier3d-compat';

export interface Physics {
  world: RAPIER.World;
  /** Dynamic box; returns its rigid body. */
  addBox(pos: [number, number, number], half: number): RAPIER.RigidBody;
}

export async function createPhysics(): Promise<Physics> {
  await RAPIER.init();
  const world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
  return {
    world,
    addBox([x, y, z], half) {
      const body = world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(x, y, z));
      world.createCollider(RAPIER.ColliderDesc.cuboid(half, half, half).setRestitution(0.3), body);
      return body;
    },
  };
}
