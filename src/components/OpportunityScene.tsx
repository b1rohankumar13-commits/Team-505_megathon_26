import { Canvas } from "@react-three/fiber";
import { ContactShadows, Environment, Lightformer, OrbitControls, useGLTF } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Box3, Vector3 } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { Pause, Play, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import ev from "@/assets/models/ev.glb.asset.json";
import home from "@/assets/models/home.glb.asset.json";
import solar from "@/assets/models/solar.glb.asset.json";
import paperless from "@/assets/models/paperless.glb.asset.json";

const MODELS: Record<string, string> = { GP01: ev.url, GP02: home.url, GP03: solar.url, GP04: paperless.url };

function ProductModel({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  const object = useMemo(() => {
    const clone = scene.clone(true);
    const bounds = new Box3().setFromObject(clone);
    const size = bounds.getSize(new Vector3());
    clone.scale.setScalar(3 / Math.max(size.x, size.y, size.z, 0.001));
    const scaled = new Box3().setFromObject(clone);
    const center = scaled.getCenter(new Vector3());
    clone.position.set(-center.x, -scaled.min.y, -center.z);
    clone.traverse((child) => { child.castShadow = true; child.receiveShadow = true; });
    return clone;
  }, [scene]);
  return <primitive object={object} rotation-y={-0.25} />;
}

export default function OpportunityScene({ productId, product }: { productId: string; product: string }) {
  const controls = useRef<OrbitControlsImpl>(null);
  const [rotating, setRotating] = useState(false);

  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    setRotating(!motion.matches);
    const update = () => setRotating(!motion.matches);
    motion.addEventListener("change", update);
    return () => motion.removeEventListener("change", update);
  }, []);

  const url = MODELS[productId];
  if (!url) return null;

  return (
    <div role="group" aria-label={`${product} 3D visual`} className="relative h-48 w-full bg-secondary/30 text-primary cursor-grab active:cursor-grabbing">
      <Canvas dpr={1} shadows camera={{ position: [4.6, 3.5, 5.2], fov: 37 }} gl={{ antialias: true, alpha: true }}>
        <ambientLight intensity={1.1} />
        <directionalLight position={[4, 7, 5]} intensity={2.2} />
        <Environment resolution={64}>
          <Lightformer intensity={2} position={[0, 5, 0]} rotation-x={Math.PI / 2} scale={[10, 10, 1]} />
          <Lightformer intensity={1.5} position={[-5, 2, 1]} rotation-y={Math.PI / 2} scale={[6, 6, 1]} />
        </Environment>
        <Suspense fallback={null}>
          <ProductModel url={url} />
        </Suspense>
        <ContactShadows position={[0, -0.01, 0]} opacity={0.3} scale={8} blur={2.5} far={4} resolution={128} frames={1} />
        <OrbitControls ref={controls} makeDefault target={[0, 0.65, 0]} enablePan={false} enableZoom={false} minPolarAngle={0.4} maxPolarAngle={Math.PI / 2.1} autoRotate={rotating} autoRotateSpeed={0.7} />
      </Canvas>
      <div className="absolute bottom-2 right-3 flex gap-1">
        <Button variant="ghost" size="icon" className="h-7 w-7 bg-card/80 text-muted-foreground" aria-label={`${rotating ? 'Pause' : 'Play'} ${product} rotation`} title={rotating ? "Pause rotation" : "Play rotation"} onClick={() => setRotating((value) => !value)}>
          {rotating ? <Pause /> : <Play />}
        </Button>
        <Button variant="ghost" size="icon" className="h-7 w-7 bg-card/80 text-muted-foreground" aria-label={`Reset ${product} view`} title="Reset view" onClick={() => controls.current?.reset()}><RotateCcw /></Button>
      </div>
    </div>
  );
}