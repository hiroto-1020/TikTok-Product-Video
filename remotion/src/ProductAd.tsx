import { AbsoluteFill, Easing, interpolate, Sequence, useCurrentFrame, useVideoConfig } from "remotion";

// 最小の雛形。Remotion を使うと判断した動画だけ、この中身を作り込む。
// ・拍 → フレーム: frame = round((beat - 1) * 60 / bpm * fps)
// ・素材は remotion/public/ に置き staticFile() で読む（scripts から input/current をコピー）
export const productAdSchema = {
  headline: "HEADLINE",
  bpm: 120,
};

type Props = typeof productAdSchema;

const beatToFrame = (beat: number, bpm: number, fps: number) => Math.round(((beat - 1) * 60 * fps) / bpm);

export const ProductAd: React.FC<Props> = ({ headline, bpm }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = interpolate(frame, [0, 8], [0.6, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(2)),
  });
  return (
    <AbsoluteFill style={{ backgroundColor: "#f4f1ec", fontFamily: "'Noto Sans JP', sans-serif" }}>
      <Sequence from={beatToFrame(1, bpm, fps)}>
        <AbsoluteFill style={{ padding: "240px 140px 480px 60px" }}>
          <div style={{ fontSize: 96, fontWeight: 900, color: "#111", transform: `scale(${pop})`, transformOrigin: "left top" }}>
            {headline}
          </div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
