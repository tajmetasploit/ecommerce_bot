{ pkgs }: {
  deps = [
    pkgs.cacert
    pkgs.glibcLocales
    pkgs.python312
    pkgs.python312Packages.pip
  ];
}
