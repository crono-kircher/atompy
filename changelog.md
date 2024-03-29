# v3.0.4
- Changed HTML theme to Furo

# v3.0.3
- Added `unroll` keyword for `atompy.subplots`

# v3.0.2
- Fixed internal import in _io.py

# v3.0.1
- Fixed internal imports

# v3.0.0
- Updated documentation
  - Expanded documentation
  - Restructured page layout
- Added `Hist1d.for_step` and `Hist1d.for_plot` methods
- Moved physics related stuff into separate submodules `atompy.physics` and
  `atompy.physics.compton_scattering`
- Added `PcolormeshData` class
- renamed `atompy.Vector.nparray` to `atompy.Vector.ndarray`.

# v2.1.0
- Updated documentation
- Added warning when `make_margins_tight` with `fixed_figwidth=True` is called
  after `change_ratio` was called
- `Hist2d.for_imshow` now returns a `ImshowData` object.
- Fixed and expanded `profile_`-methods for `Hist2d`


# v2.0.0
- changed return value when loading multiple histos at once
- changed that the _histXd functions return Hist1d and Hist2d instances
