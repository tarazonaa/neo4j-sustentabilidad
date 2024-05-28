import { useEffect } from "react";

import type { FrameData } from "@/types.ts";

export const useAnimate = (
  frameData: FrameData | null,
) => {
  useEffect(() => {
    if (!frameData) return;

    frameData.controls && frameData.controls.update();

    const animate = () => {
      const { scene, camera, controls, renderers } = frameData as FrameData;
      
      camera && camera.lookAt(scene.position);
      controls && controls.update();

      renderers?.forEach((r) => {
        r.render(scene, camera);
      });
      requestAnimationFrame(animate);
    };
    animate()
  }, [frameData])
}