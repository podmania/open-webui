{
  description = "Open-webui distroless image using nix2container";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nix2container.url = "github:nlewo/nix2container";
    base.url = "github:podmania/base";
  };

  outputs = { self, nixpkgs, nix2container, base }: let
    system = builtins.currentSystem;
    pkgs = nixpkgs.legacyPackages.${system};
    n2c = nix2container.outputs.packages.${system}.nix2container;
    pkg = pkgs.open-webui;
    imageConfig = {
      ExposedPorts = {
        "8080/tcp" = {};
      };
      Volumes = {
        "/app/backend/data" = {};
      };
      Env = [
          "ENABLE_OLLAMA_API=False"
          "DATA_DIR=/app/backend/data"
          "HF_HOME=/app/backend/data/huggingface"
          "STATIC_DIR=/app/backend/data/static"
      ];
      Cmd = [ "${pkg}/bin/open-webui" "serve" ];
    };
  in {
    packages.${system} = {
      open-webui-image = n2c.buildImage {
        name = "open-webui";
        tag = "latest";
        fromImage = base.packages.${system}.base-image;
        maxLayers = 5;
        copyToRoot = [ pkgs.ffmpeg-headless ];
        config = imageConfig;
      };

      open-webui-debug-image = n2c.buildImage {
        name = "open-webui";
        tag = "latest-debug";
        fromImage = base.packages.${system}.base-debug-image;
        maxLayers = 5;
        copyToRoot = [ pkgs.ffmpeg-headless ];
        config = imageConfig;
      };

      open-webui = pkg;

      default = self.packages.${system}.open-webui-image;
    };

    version = pkg.version;
  };
}
