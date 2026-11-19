import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// "angle" uses the GPU through Chrome on Windows; much faster than software GL.
Config.setChromiumOpenGlRenderer("angle");
