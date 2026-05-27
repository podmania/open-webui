{
  description = "<%= name.capitalize() %> distroless image using nix2container";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nix2container.url = "github:nlewo/nix2container";
    base.url = "github:podmania/base";
  };

  outputs = { self, nixpkgs, nix2container, base }: let
    system = builtins.currentSystem;
    pkgs = nixpkgs.legacyPackages.${system};
    n2c = nix2container.outputs.packages.${system}.nix2container;
    version = "0.0.0";
    srcHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    pkg = pkgs.<%= name %>.overrideAttrs (old: {
      inherit version;
      src = pkgs.<%= fetcher %> {
        url = "<%= fetch_url %>";
        hash = srcHash;
      };
    });
    imageConfig = {
      ExposedPorts = {
        <% for port in ports %>
        "<%= port %>/tcp" = {};
        <% endfor %>
      };
      Volumes = {
        <% for volume in volumes %>
        "<%= volume %>" = {};
        <% endfor %>
      };
      <% if env %>
      Env = [
        <% for e in env %>
        "<%= e %>"
        <% endfor %>
      ];
      <% endif %>
      Cmd = [ "${pkg}/bin/<%= main_program or name %>"<% for arg in cmd_args %> "<%= arg %>"<% endfor %> ];
    };
  in {
    packages.${system} = {
      <%= name %>-image = n2c.buildImage {
        name = "<%= name %>";
        tag = "latest";
        fromImage = base.packages.${system}.base-image;
        maxLayers = 5;
        config = imageConfig;
      };

      <%= name %>-debug-image = n2c.buildImage {
        name = "<%= name %>";
        tag = "latest-debug";
        fromImage = base.packages.${system}.base-debug-image;
        maxLayers = 5;
        config = imageConfig;
      };

      <%= name %> = pkg;

      default = self.packages.${system}.<%= name %>-image;
    };

    <%= name %>Version = version;
  };
}
