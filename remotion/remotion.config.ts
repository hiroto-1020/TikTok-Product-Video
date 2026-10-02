import { Config } from "@remotion/cli/config";

// TikTok 縦型の共通仕様（HyperFrames 側と同じ）
Config.setVideoImageFormat("png"); // png → yuv420p（jpeg だと yuvj420p になる）
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
Config.setOverwriteOutput(true);
