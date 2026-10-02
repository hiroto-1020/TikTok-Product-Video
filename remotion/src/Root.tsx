import { Composition } from "remotion";
import { ProductAd, productAdSchema } from "./ProductAd";

// 1080x1920 / 30fps。尺は Beat Grid（planning/shot-plan.json）の duration_frames に合わせて変更する。
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ProductAd"
      component={ProductAd}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={20 * 30}
      defaultProps={productAdSchema}
    />
  );
};
