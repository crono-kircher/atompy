import io
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
import matplotlib.colorbar
from matplotlib.text import Text
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.gridspec import SubplotSpec, GridSpec
from matplotlib.transforms import Bbox
from matplotlib.cm import ScalarMappable
import numpy as np
from numpy.typing import ArrayLike, NDArray
from typing import Optional, Literal, Union, Any, NamedTuple, Sequence
from dataclasses import dataclass


PTS_PER_INCH = 72.0
"""float: 72 pts = 1 inch"""

MM_PER_INCH = 25.4
"""float: 25.4 mm = 1 inch"""

_COLORBAR_LABEL = "atompy colorbar axes"

RED = "#AE1117"
TEAL = "#008081"
BLUE = "#2768F5"
GREEN = "#007F00"
GREY = "#404040"
ORANGE = "#FD8D3C"
PINK = "#D4B9DA"
YELLOW = "#FCE205"
LEMON = "#EFFD5F"
CORN = "#E4CD05"
PURPLE = "#CA8DFD"
DARK_PURPLE = "#9300FF"
FOREST_GREEN = "#0B6623"
BRIGHT_GREEN = "#3BB143"


class _Colors(NamedTuple):
    red: Literal["#AE1117"]
    blue: Literal["#2768F5"]
    orange: Literal["#FD8D3C"]
    pink: Literal["#D4B9DA"]
    green: Literal["#007F00"]
    teal: Literal["#008081"]
    grey: Literal["#404040"]
    yellow: Literal["#FCE205"]
    lemon: Literal["#EFFD5F"]
    corn: Literal["#E4CD05"]
    purple: Literal["#CA8DFD"]
    dark_purple: Literal["#9300FF"]
    forest_green: Literal["#0B6623"]
    bright_green: Literal["#3BB143"]


colors = _Colors(
    RED, BLUE, ORANGE, PINK, GREEN, TEAL, GREY,
    YELLOW, LEMON, CORN, PURPLE,
    DARK_PURPLE, FOREST_GREEN, BRIGHT_GREEN)


_font_scalings = {
    'xx-small': 0.579,
    'x-small': 0.694,
    'small': 0.833,
    'medium': 1.0,
    'large': 1.200,
    'x-large': 1.440,
    'xx-large': 1.728,
    'larger': 1.2,
    'smaller': 0.833}


class AliasError(Exception):
    def __init__(self,
                 keyword_arg: str,
                 alias: str):
        self.keyword_arg = keyword_arg
        self.alias = alias

    def __str__(self):
        return (f"Both '{self.keyword_arg}' and '{self.alias}' have been "
                "provided, but they are aliases")


class FigureWidthTooLargeError(Exception):
    def __str__(self):
        return (
            "New figure width exceeds maximum allowed figure width"
        )


@dataclass
class _Colorbar:
    colorbar: matplotlib.colorbar.Colorbar
    parent_ax: Axes
    location: Literal["left", "right", "top", "bottom"]
    thickness_inch: float
    pad_inch: float

    @property
    def ax(self) -> Axes:
        return self.colorbar.ax


class _ColorbarManager:
    def __init__(self) -> None:
        self.colorbars: list[_Colorbar] = []


_colorbar_manager = _ColorbarManager()


@dataclass
class Edges:
    """
    Wrapper for things that are at the left, right, top, bottom edge of
    something (e.g., the margins of a ``matplotlib.axes.Axes``.

    Parameters
    ----------
    left, right, top, bottom : Any
    """
    left: Any
    right: Any
    top: Any
    bottom: Any

    def __iter__(self):
        for item in [self.right, self.left, self.top, self.bottom]:
            yield item

    def __getitem__(self, key: Union[int, str]) -> NDArray[np.float64]:
        if isinstance(key, str):
            key = ["left", "right", "top", "bottom"].index(key)
        return [self.left, self.right, self.top, self.bottom][key]

    def __len__(self) -> int: return 4


def clear_colorbars() -> None:
    """
    Clear reference to all colorbars that were created by :func:`add_colorbar`.

    You probably never have to call this.

    Notes
    -----
    ``atompy`` keeps track of all colorbars added by :func:`add_colorbar` in
    a list. This list is not cleared, even if one closes the figure within
    which the colorbar is contained.

    Calling ``clear_colorbars`` clears that list.
    """
    del _colorbar_manager.colorbars[:]


cm_lmf2root = LinearSegmentedColormap.from_list(
    "lmf2root",
    [(0.0, (0.5, 1.0, 1.0)),
     (0.3, (0.0, 0.0, 1.0)),
     (0.7, (1.0, 0.0, 0.0)),
     (1.0, (1.0, 1.0, 0.0))]
)
matplotlib.colormaps.register(cm_lmf2root, force=True)
cm_lmf2root_from_white = LinearSegmentedColormap.from_list(
    "lmf2root_from_white",
    [(0.0, (1.0, 1.0, 1.0)),
     (0.65, (0.5, 1.0, 1.0)),
     (0.3, (0.0, 0.0, 1.0)),
     (0.7, (1.0, 0.0, 0.0)),
     (1.0, (1.0, 1.0, 0.0))]
)
matplotlib.colormaps.register(cm_lmf2root_from_white, force=True)


def textwithbox(
    axes: Axes,
    x: float,
    y: float,
    text: str,
    pad: float = 1.0,
    boxbackground: Optional[str] = "white",
    boxedgecolor: str = "black",
    boxedgewidth: float = 0.5,
    **text_kwargs
) -> Text:
    """
    Plot text with matplotlib surrounded by a box. Only works with a
    latex backend

    Parameters
    ----------
    ax : ``matplotlib.axes.Axes``
        the axes

    x : float
        x-position

    y : float
        y-position

    text : str
        The text to be surrounded by the box

    pad : float, default: :code:`1.0` (in pts)
        padding between boxedge and text

    boxbackground : ``None``, ``False``, or str, default: ``"white"``
        background of box

        - ``None`` or ``False``: No background color
        - str: latex xcolor named color

    boxedgecolor : str, optional, default: :code:`"black"`
        edge color using named color from latex package *xcolor*
        only used if boxbackground != None

    boxedgewidth : float, default :code:`0.5` (in pts)
        edgelinewidth of the box

    **text_kwargs : ``matpotlib.text.Text``

    Returns
    -------
    text ``matplotlib.text.Text``
        The text artist.

    Other Parameters
    ----------------
properties
        Other miscellaneous text parameters
    """
    sep = r"\setlength{\fboxsep}{%lfpt}" % pad
    rule = r"\setlength{\fboxrule}{%lfpt}" % boxedgewidth
    if boxbackground is not None:
        text = r"%s\fcolorbox{%s}{%s}{%s}" % (sep + rule, boxedgecolor,
                                              boxbackground, text)
    else:
        text = r"%s\fbox{%s}" % (sep + rule, text)
    return axes.text(x, y, text, **text_kwargs)


def _set_lw_fs_lh(
    linewidth: Optional[float],
    fontsize: Optional[Union[float, str]],
    legend_handlelength: Optional[float],
    **aliases
) -> tuple[float, float, float]:
    """ Process parameters for dashed/dotted/... """
    # check if aliases are doubled
    if "lw" in aliases and linewidth is not None:
        raise AliasError("linewidth", "lw")
    if "lh" in aliases and legend_handlelength is not None:
        raise AliasError("legend_handlelength", "lh")

    lw = linewidth if linewidth else \
        aliases.get("lw", plt.rcParams["lines.linewidth"])
    lh = legend_handlelength if legend_handlelength else \
        aliases.get("lh", plt.rcParams["legend.handlelength"])
    fontsize_ = (fontsize if fontsize is not None
                 else plt.rcParams["legend.fontsize"])
    if isinstance(fontsize_, str):
        if fontsize_ in _font_scalings:
            fontsize_ = _font_scalings[fontsize_] * plt.rcParams["font.size"]
        else:
            raise ValueError("Invalid specifier for fontsize")

    return lw, fontsize_, lh


def dotted(
    linewidth: Optional[float] = None,
    fontsize: Optional[Union[float,
                             Literal["xx-small", "x-small", "small", "medium",
                                     "large", "x-large", "xx-large", "larger",
                                     "smaller"]
                             ]] = None,
    legend_handlelength: Optional[float] = None,
    **aliases
) -> tuple[float, tuple[float, float]]:
    """
    Return a ls tuple to create a dotted line that fits perfectly into a
    legend. For that to work properly you may need to provide the linewidth of
    the graph and the fontsize of the legend.

    Parameters
    ----------
    linewidth (or lw) : float, optional, default: ``rcParams["lines.linewidth"]``

    fontsize : float or str, Optional, default: ``rcParams["legend.fontsize"]``
        The fontsize used in the legend

        - float: fontsize in pts
        - str: :code:`"xx-small"`, :code:`"x-small"`, :code:`"small"`,
          :code:`"medium"`, :code:`"large"`, :code:`"x-large"`, 
          :code:`"xx-large"`, :code:`"larger"`, or :code:`"smaller"`

    legend_handlelength (or lh) : float, default ``rcParams["legend.handlelength"]``
        Length of the legend handles (the dotted line, in this case) in font
        units

    Returns
    -------
    tuple : (float, (float, float))
        tuple to be used as linetype in plotting

    Examples
    --------
    .. code-block:: python

        import matplotlib.pyplot as plt
        import atompy as ap

        plt.plot([0., 1.], linestyle=ap.dotted())
        plt.legend()

        # if one changes the linewidth, the fontsize of the legend, or the
        # handlelength of the legend from the default, this needs to be passed
        # to dotted().
        plt.plot([0., 1.],
                 linewidth=2.,
                 linestyle=(ap.dotted(linewidth=2.,
                                      legend_handlelength=3.,
                                      fontsize="x-small")))
        plt.legend(fontsize="x-small", handlelength=3.)

        # alternatively, use rcParams to set these values
        plt.rcParams["lines.linewidth"] = 2.
        plt.rcParams["legend.handlelength"] = 3.
        plt.rcParams["legend.fontsize"] = "x-small"
        plt.plot([0., 1.], linestyle=ap.dotted())
        plt.legend()
    """
    lw_, fs_, lh_ = _set_lw_fs_lh(
        linewidth, fontsize, legend_handlelength, **aliases)

    total_points = fs_ * lh_ / lw_
    n_dots = math.ceil(total_points / 2.0)
    spacewidth = (total_points - n_dots) / (n_dots - 1)

    return 0.0, (1.0, spacewidth)


def dash_dotted(
    ratio: float = 3.0,
    n_dashes: int = 3,
    linewidth: Optional[float] = None,
    fontsize: Optional[Union[float,
                             Literal["xx-small", "x-small", "small", "medium",
                                     "large", "x-large", "xx-large", "larger",
                                     "smaller"]
                             ]] = None,
    legend_handlelength: Optional[float] = None,
    **aliases
) -> tuple[float, tuple[float, float, float, float]]:
    """
    Return a ls tuple to create a dash-dotted line that fits perfectly into a
    legend. For that to work properly you may need to provide the linewidth of
    the graph and the fontsize of the legend.

    Parameters
    ----------
    ratio : float, default: 3.0
        Ratio between dash-length and gap-length

    n_dashes : int, default: 3
        Number of dashes drawn

    linewidth (or lw) : float, optional, default: ``rcParams["lines.linewidth"]``

    fontsize : float or str, Optional, default: ``rcParams["legend.fontsize"]``
        The fontsize used in the legend

        - float: fontsize in pts
        - str: :code:`"xx-small"`, :code:`"x-small"`, :code:`"small"`,
          :code:`"medium"`, :code:`"large"`, :code:`"x-large"`, 
          :code:`"xx-large"`, :code:`"larger"`, or :code:`"smaller"`

    legend_handlelength (or 'lh') : float, default :code:`rcParams["legend.handlelength"]`
        Length of the legend handles (the dotted line, in this case) in font
        units

    Returns
    -------
    tuple : (float, (float, float, float, float))
        tuple to be used as linetype in plotting

    Examples
    --------
    See :func:`.dotted`.
    """
    lw_, fs_, lh_ = _set_lw_fs_lh(
        linewidth, fontsize, legend_handlelength, **aliases)

    total_points = fs_ * lh_ / lw_
    spacewidth = (total_points - n_dashes) / \
                 (2.0 * n_dashes - 1 + n_dashes * ratio)
    dashwidth = ratio * spacewidth

    return 0.0, (dashwidth, spacewidth, 1.0, spacewidth)


def dashed(
    ratio: float = 1.5,
    n_dashes: int = 4,
    linewidth: Optional[float] = None,
    fontsize: Optional[Union[float,
                             Literal["xx-small", "x-small", "small", "medium",
                                     "large", "x-large", "xx-large", "larger",
                                     "smaller"]
                             ]] = None,
    legend_handlelength: Optional[float] = None,
    **aliases
) -> tuple[float, tuple[float, float]]:
    """
    Return a ls tuple to create a dashed line that fits perfectly into a
    legend. For that to work properly you may need to provide the linewidth of
    the graph and the fontsize of the legend.

    Parameters
    ----------
    ratio : float, default: 1.5
        Ratio between dash-length and gap-length

    n_dashes : int, default: 4
        Number of dashes drawn

    linewidth (or lw) : float, optional, default: rcParams["lines.linewidth"]

    fontsize : float or str, Optional, default: rcParams["legend.fontsize"]
        The fontsize used in the legend

        - float: fontsize in pts
        - str: :code:`"xx-small"`, :code:`"x-small"`, :code:`"small"`,
          :code:`"medium"`, :code:`"large"`, :code:`"x-large"`, 
          :code:`"xx-large"`, :code:`"larger"`, or :code:`"smaller"`

    legend_handlelength (or lh) : float, default \
:code:`rcParams["legend.handlelength"]`
        Length of the legend handles (the dotted line, in this case) in font
        units

    Returns
    -------
    (float, (float, float, float, float))
        tuple to be used as linetype in plotting

    Examples
    --------
    See :func:`.dotted`.
    """
    lw_, fs_, lh_ = _set_lw_fs_lh(
        linewidth, fontsize, legend_handlelength, **aliases)

    total_points = fs_ * lh_ / lw_

    n_gaps = n_dashes - 1
    spacewidth = total_points / (n_gaps + n_dashes * ratio)
    dashwidth = ratio * spacewidth

    return 0.0, (dashwidth, spacewidth)


def add_colorbar(
        mappable: ScalarMappable,
        ax: Optional[Axes] = None,
        location: Literal["left", "right", "top", "bottom"] = "right",
        thickness_pts: Optional[float] = None,
        pad_pts: Optional[float] = None,
) -> matplotlib.colorbar.Colorbar:
    """
    Add a colorbar to `axes`.

    Create a new ``matplotlib.axes.Axes`` next to `ax` with the same height
    (or width), then plot a ``matplotlib.color.Colorbar`` in it.

    If you change the figure-layout after the fact, you can update the colorbar
    position with :func:`.update_colorbars`.

    Parameters
    ----------
    mappable : ``matplotlib.cm.ScalarMappable``
        The colormap described by this colorbar.

        For more information, see
        `matplotlib.pyplot.colorbar <https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.colorbar.html>`_.

    ax : ``matplotlib.axes.Axes``, optional
        The axes to which the colorbar is added.

        If ``None``, use currently active axes.

    location : {'left', 'right', 'top', 'bottom'}, default: ``right``
        Location of the colorbar relative to `ax`.

    thickness_pts : float, optional
        The thickness of the colorbar in pts.

        If ``None``, the width will be 5% of the current width (or height,
        depending on `location`) of the axes.

    pad_pts : float, optional
        The pad between the colorbar and `axes` in pts.

        If ``None``, the pad will be 60% of `thickness_pts`.

    Returns
    -------
    colorbar : ``matplotlib.colorbar.Colorbar``

    Examples
    --------
    .. code-block:: python

        im = plt.imshow()
        ap.add_colorbar(im)

        fig, axs = plt.subplots(1, 2)

        im0 = axs[0].imshow()
        im1 = axs[1].imshow()

        cb0 = ap.add_colorbar(im0, axs[0], location="top")
        cb1 = ap.add_colorbar(im1, axs[1], location="bottom")

        for cb in [cb0, cb1]:
            cb.set_label("Colorbar Label")
    """
    valid_positions = ["left", "right", "top", "bottom"]
    if location not in valid_positions:
        msg = f"{location=}, but it should be in {valid_positions}"
        raise ValueError(msg)

    DEFAULT_THICKNESS = 0.05
    DEFAULT_PAD = 0.6

    ax = ax or plt.gca()
    fig = plt.gcf()
    fig_width, fig_height = fig.get_size_inches()
    bbox = ax.get_position()

    if location in ["left", "right"]:
        fig_size = fig_width
        bbox_size = bbox.width
    elif location in ["top", "bottom"]:
        fig_size = fig_height
        bbox_size = bbox.height

    if thickness_pts is None:
        thickness = bbox_size * DEFAULT_THICKNESS
    else:
        thickness = thickness_pts / PTS_PER_INCH / fig_size

    if pad_pts is None:
        pad = thickness * DEFAULT_PAD
    else:
        pad = pad_pts / PTS_PER_INCH / fig_size

    if location == "left":
        height = bbox.height
        width = thickness
        x0 = bbox.x0 - pad - width
        y0 = bbox.y0

    elif location == "right":
        width = thickness
        height = bbox.height
        x0 = bbox.x1 + pad
        y0 = bbox.y0

    elif location == "top":
        width = bbox.width
        height = thickness
        x0 = bbox.x0
        y0 = bbox.y1 + pad

    elif location == "bottom":
        width = bbox.width
        height = thickness
        x0 = bbox.x0
        y0 = bbox.y0 - pad - height

    colorbar_axes = fig.add_axes(
        (x0, y0, width, height), label=_COLORBAR_LABEL)
    colorbar = fig.colorbar(mappable, cax=colorbar_axes, location=location)

    _colorbar_manager.colorbars.append(
        _Colorbar(colorbar, ax, location, thickness*fig_size, pad*fig_size)
    )
    return colorbar


def assign_colorbar_to_ax(
        colorbar: matplotlib.colorbar.Colorbar,
        ax: Axes,
        ax1: Optional[Axes] = None,
        location: Literal["auto", "left", "right", "top", "bottom"] = "auto"
) -> None:
    if ax1 is not None:
        raise NotImplementedError
    raise NotImplementedError


def add_abc(
        fig: Optional[Figure] = None,
        xoffset_pts: float = 2.0,
        yoffset_pts: float = -12.0,
        anchor: Literal["top left", "top right",
                        "bottom left", "bottom right"] = "top left",
        labels: Optional[str] = "a b c d e f g h i j k l m n o p q r s t u v w x y z",
        pre: str = "(",
        post: str = ")",
        start_at: int = 0,
        rowsfirst: bool = True,
        **text_kwargs
) -> dict[Axes, Text]:
    """
    Add labels to all suplots in `fig`.

    By default, adds '(a)', '(b)', ... to each subplot in the upper-right
    corner.

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        If ``None``, use last active figure.

    xoffset_pts : float, default ``2.0``
        Offset in pts from `anchor`. Positive moves right.

    yoffset_pts : float, default ``-12.0``
        Offset in pts from `anchor`. Positive moves up.

    anchor : {``"top left"``, ``"top right"``, ``"bottom left"``, ``"bottom right"``}
        Specify anchor point of the labels (offsets are relative to this).
        Refers to the corner of the graph-area of the axes.

    labels : str, optional
        A string of labels, where each label is seperated by a space.

        If ``None``, use label of the respective axes
        (i.e., ``ax.get_label()``).

    pre : str, default ``"("``
        String in front of `labels`. Applies only if `labels` is not ``None``.

    post : str, default ``")"``
        String after `labels`. Applies only if `labels` is not ``None``.

    start_at : int, default 0
        Skip `start_at` entries in `labels`. Only applies if `labels` is not
        ``None``.

    rowsfirst : bool, default ``True``
        Label rows first, e.g., "a b c / d e f" instead of "a c e / b d f".
        Only applies if `labels` is not ``None``.

    text_kwargs
        Additional keyword arguments of ``matplotlib.text.Text``.

    Returns
    -------
    text_dict : dict[``matplotlib.axes.Axes``, ``matplotlib.text.Text``]
        A dictionary with the axes of `fig` as keys and the corresponding
        text instances added by ``add_abc`` as values.

        Can be used to manipulate the text later (to, e.g., change the color
        of the text only for certain subplots).

    Notes
    -----
    - Cannot handle fancy GridSpecs, e.g., where one
      subplot spans multiple other subplots.
      If you need one of those, you're on your own.

    - :func:`make_me_nice` does not see the added labels. If your labels extent
      further than the current axes dimensions, they will be cut of when calling
      ``make_me_nice``. To alleviate the problem, apply additional margins
      in ``make_me_nice``.
    """
    fig = fig or plt.gcf()
    axs = get_sorted_axes_grid(fig)
    nrows, ncols = axs.shape

    bboxes_inch = np.empty((nrows, ncols), dtype=Bbox)

    valid_anchors = ["top left", "top right", "bottom left", "bottom right"]
    if anchor not in valid_anchors:
        err_msg = (f"{anchor=}, but it needs to be one of {valid_anchors}")
        raise ValueError(err_msg)
    topbottom = anchor.split(" ")[0]
    leftright = anchor.split(" ")[1]
    refs_hori_inch = np.empty((nrows, ncols), dtype=Bbox)
    refs_vert_inch = np.empty((nrows, ncols), dtype=Bbox)

    if labels is not None:
        labels_ = labels.split(" ")
    text: list[list[str]] = []

    for row in range(nrows):
        text.append([])
        for col in range(ncols):
            bboxes_inch[row, col] = get_axes_position_inch(axs[row, col])

            if leftright == "left":
                refs_hori_inch[row, col] = bboxes_inch[row, col].x0
            else:  # right
                refs_hori_inch[row, col] = bboxes_inch[row, col].x1
            if topbottom == "top":
                refs_vert_inch[row, col] = bboxes_inch[row, col].y1
            else:  # bottom
                refs_vert_inch[row, col] = bboxes_inch[row, col].y0

            if labels is None:
                text[row].append(str(axs[row, col].get_label()))
            else:
                if rowsfirst:
                    text[row].append(
                        pre + labels_[start_at + ncols*row + col] + post)
                else:
                    text[row].append(
                        pre + labels_[start_at + nrows*col + row] + post)

    xoffset_inch = xoffset_pts / PTS_PER_INCH
    yoffset_inch = yoffset_pts / PTS_PER_INCH
    x_positions_inch = np.empty((nrows, ncols))
    y_positions_inch = np.empty((nrows, ncols))

    for row in range(nrows):
        for col in range(ncols):
            if leftright == "left":
                x_positions_inch[row, col] = \
                    xoffset_inch / bboxes_inch[row, col].width
            else:
                x_positions_inch[row, col] = \
                    1.0 + xoffset_inch / bboxes_inch[row, col].width
            if topbottom == "top":
                y_positions_inch[row, col] = \
                    1.0 + yoffset_inch / bboxes_inch[row, col].height
            else:
                y_positions_inch[row, col] = \
                    yoffset_inch / bboxes_inch[row, col].height

    text_kwargs.setdefault("clip_on", False)

    out: dict[Axes, Text] = {}
    for row in range(nrows):
        for col in range(ncols):
            out[axs[row, col]] = axs[row, col].text(
                x_positions_inch[row, col],
                y_positions_inch[row, col],
                text[row][col],
                transform=axs[row, col].transAxes,
                **text_kwargs)

    return out


def update_colorbars(fig: Optional[Figure] = None) -> None:
    """
    Re-align colorbars to their parent axes.

    Only re-aligns colorbars added by :func:`.add_colorbar`.

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        If ``None``, use last active figure.
    """
    fig = fig or plt.gcf()
    fig_width_inch, fig_height_inch = fig.get_size_inches()
    axs = fig.get_axes()

    for colorbar in _colorbar_manager.colorbars:
        # check that colorbar is actually in the figure. If not: Skip
        if colorbar.ax not in axs:
            continue

        bbox_ax = colorbar.parent_ax.get_position()

        if colorbar.location in ["left", "right"]:
            pad = colorbar.pad_inch / fig_width_inch
            thickness = colorbar.thickness_inch / fig_width_inch
        elif colorbar.location in ["top", "bottom"]:
            pad = colorbar.pad_inch / fig_height_inch
            thickness = colorbar.thickness_inch / fig_height_inch

        if colorbar.location == "left":
            colorbar.ax.set_position((
                bbox_ax.x0 - pad - thickness,
                bbox_ax.y0,
                thickness,
                bbox_ax.height
            ))
        if colorbar.location == "right":
            colorbar.ax.set_position((
                bbox_ax.x1 + pad,
                bbox_ax.y0,
                thickness,
                bbox_ax.height
            ))
        if colorbar.location == "top":
            colorbar.ax.set_position((
                bbox_ax.x0,
                bbox_ax.y1 + pad,
                bbox_ax.width,
                thickness
            ))
        if colorbar.location == "bottom":
            colorbar.ax.set_position((
                bbox_ax.x0,
                bbox_ax.y0 - pad - thickness,
                bbox_ax.width,
                thickness
            ))


def get_renderer(fig: Optional[Figure]) -> RendererBase:
    """
    Get the renderer of the `fig`.

    Taken from https://stackoverflow.com/questions/22667224/get-text-bounding-box-independent-of-backend/

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        If ``None``, use last active figure.

    Returns
    -------
    renderer : ``matplotlib.matplotlib.backend_bases.RendererBase``
    """
    fig = fig or plt.gcf()
    if hasattr(fig.canvas, "get_renderer"):
        # Some backends, such as TkAgg, have the get_renderer method, which
        # makes this easy.
        renderer = fig.canvas.get_renderer()  # type: ignore
    else:
        # Other backends do not have the get_renderer method, so we have a work
        # around to find the renderer.  Print the figure to a temporary file
        # object, and then grab the renderer that was used.
        # (I stole this trick from the matplotlib backend_bases.py
        # print_figure() method.)
        fig.canvas.print_pdf(io.BytesIO())  # type: ignore
        renderer = fig._cachedRenderer  # type: ignore
    return (renderer)


def set_axes_size(
    width_inch: float,
    height_inch: float,
    ax: Optional[Axes] = None,
    anchor: Literal["center", "left", "right", "upper", "lower",
                    "upper left", "upper right", "upper center",
                    "center left", "center right", "center center",
                    "lower left", "lower right", "lower center"] = "center",
) -> None:
    """
    Set physical size of `ax`.

    Parameters
    ----------
    width_inch, height_inch : float
        New width and height of the graph-area of `ax`.

    ax : ``matplotlib.pyplot.Axes``, optional
        If ``None``, change last active axes.

    anchor : {``"left"``, ``"right"``, ``"upper"``, ``"lower"``, \
``"upper left"``, ``"upper right"``, ``"upper center"``, \
``"center left"``, ``"center right"``, ``"center center"``, \
``"lower left"``, ``"lower right"``, ``"lower center"``}, default "center",
        Anchor point of `ax`.

        E.g., ``"upper left"`` means the upper left corner of `ax` stays fixed.
    """
    @dataclass
    class Position:
        x0: float
        y0: float
        width: float
        height: float

    fw_inch, fh_inch = plt.gcf().get_size_inches()
    ax = ax or plt.gca()
    ax.set_adjustable("datalim")

    old_pos = ax.get_position()
    new_pos = Position(old_pos.x0, old_pos.y0,
                       width_inch / fw_inch, height_inch / fh_inch)

    if anchor == "center":
        anchor = "center center"
    elif anchor == "left":
        anchor = "center left"
    elif anchor == "right":
        anchor = "center right"
    elif anchor == "upper":
        anchor = "upper center"
    elif anchor == "lower":
        anchor = "lower center"

    anchor_split = anchor.split()

    if anchor_split[0] == "lower":
        pass
    elif anchor_split[0] == "upper":
        new_pos.y0 = old_pos.y0 + (old_pos.height - new_pos.height)
    elif anchor_split[0] == "center":
        new_pos.y0 = old_pos.y0 + (old_pos.height - new_pos.height) / 2.0

    if anchor_split[1] == "left":
        pass
    elif anchor_split[1] == "right":
        new_pos.x0 = old_pos.x0 + (old_pos.width - new_pos.width)
    elif anchor_split[1] == "center":
        new_pos.x0 = old_pos.x0 + (old_pos.width - new_pos.width) / 2.0

    ax.set_position((new_pos.x0, new_pos.y0,
                     new_pos.width, new_pos.height))

    update_colorbars()


def get_sorted_axes_grid(fig: Optional[Figure] = None) -> NDArray:
    """
    Get all axes from `fig` and sort them into a 2D grid.

    Only works if all axes of `fig` are part of one-and-the-same
    ``matplotlib.gridspec.GridSpec`` and if axes are indeed aranged
    in a 2D grid.

    Ignores colormap axes added by :func:`.add_colorbar`.

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        If ``None``, use last active figure.

    Returns
    -------
    axes_grid : ``numpy.ndarray``, shape ``(nrows, ncols)``
        A 2D numpy array containing the axes of `fig`.

        ``axes_grid[0, 0]`` refers to the top-left,
        ``axes_grid[nrows-1, ncols-1]`` to the bottom right corner.
    """
    fig = fig or plt.gcf()

    axs_unordered: list[Axes] = []
    for ax in fig.get_axes():
        if ax.get_label() != _COLORBAR_LABEL:
            axs_unordered.append(ax)

    # get subplotspecs, ensureing that it is not None
    subplotspecs: dict[Axes, SubplotSpec] = {}
    for ax in axs_unordered:
        subplotspec = ax.get_subplotspec()
        if subplotspec is None:
            msg = "axes not part of a GridSpec, this won't work"
            raise ValueError(msg)
        else:
            subplotspecs[ax] = subplotspec
    assert subplotspecs, "subplotspecs were empty here"

    # check that there is only one GridSpec in the figure
    gridspec = subplotspecs[axs_unordered[0]].get_gridspec()
    for subplotspec in subplotspecs.values():
        if subplotspec.get_gridspec() is not gridspec:
            raise ValueError("Multiple GridSpecs in figure, this won't work")
        if subplotspec.num1 != subplotspec.num2:
            msg = "GridSpec too fancy for me. I can't handle this :c"
            raise ValueError(msg)

    # create a ndarray of axes aranged in a grid corresponding to the gridspec
    axs = np.empty((gridspec.nrows, gridspec.ncols), dtype=Axes)
    for row in range(gridspec.nrows):
        for col in range(gridspec.ncols):
            for ax in axs_unordered:
                if subplotspecs[ax] == gridspec[row, col]:
                    axs[row, col] = ax

    return axs


def get_column_pads_inches(fig: Optional[Figure] = None) -> NDArray[np.float_]:
    """
    Get distance between columns of axes in inches.

    Only works if all axes of `fig` are part of one-and-the-same
    ``matplotlib.gridspec.GridSpec`` and if axes are indeed aranged
    in a 2D grid.

    Ignores colormap axes added by :func:`.add_colorbar`.

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        If ``None``, use last active figure.

    Returns
    -------
    xpads_inches : ``numpy.ndarray``, shape ``(nrows, ncols-1)``
        2D numpy array of the distance in-between columns in inch.
    """
    fig = fig or plt.gcf()
    fig_width_inch, _ = fig.get_size_inches()

    axs = get_sorted_axes_grid(fig)
    gridspec: GridSpec = axs[0, 0].get_subplotspec().get_gridspec()

    if gridspec.ncols == 1:
        raise ValueError("Only one column in 'fig'")

    xpads_inch = np.empty((gridspec.nrows, gridspec.ncols-1), dtype=Axes)
    for row in range(gridspec.nrows):
        for col in range(gridspec.ncols-1):
            bbox0 = axs[row, col].get_position()
            bbox1 = axs[row, col+1].get_position()
            xpads_inch[row, col] = (bbox1.x0 - bbox0.x1) * fig_width_inch

    return xpads_inch


def set_min_column_pads(
    column_pad_pts: ArrayLike,
    fig: Optional[Figure] = None
) -> None:
    """
    Set the minimum distance between columns.

    Parameters
    ----------
    xpads_pts: ArrayLike
        The desired minimum distance in pts.

        You can pass a single float or number-of-columns floats.

    fig : ``matplotlib.figure.Figure``, optional
        If ``None``, use last active figure.
    """
    fig = fig or plt.gcf()
    fw_inch, _ = fig.get_size_inches()

    axs = get_sorted_axes_grid(fig)
    gridspec: GridSpec = axs[0, 0].get_subplotspec().get_gridspec()
    if gridspec.ncols == 1:
        raise ValueError("Only one column in 'fig'")

    xpads_inch = np.array(column_pad_pts) / fw_inch
    if xpads_inch.size == 1:
        value = xpads_inch[0] if xpads_inch.shape else xpads_inch
        xpads_inch = np.full(gridspec.ncols-1, value)
    elif xpads_inch.shape != (gridspec.ncols-1,):
        msg = (
            f"len(xpad_pts)={xpads_inch.size}, but it should be "
            f"{gridspec.ncols-1}"
        )
        raise ValueError(msg)

    deltas = np.min(get_column_pads_inches(fig), axis=0) - xpads_inch
    for row in range(gridspec.nrows):
        for col in range(1, gridspec.ncols):
            bbox = axs[row, col].get_position()
            axs[row, col].set_position((
                bbox.x0 - col*deltas[col-1] / fw_inch,
                bbox.y0,
                bbox.width,
                bbox.height
            ))

    update_colorbars()


def get_row_pads_inches(fig: Optional[Figure] = None) -> NDArray:
    """
    Get distance between rows of axes in inches.

    Only works if all axes of `fig` are part of one-and-the-same
    ``matplotlib.gridspec.GridSpec`` and if axes are indeed aranged
    in a 2D grid.

    Ignores colormap axes added by :func:`.add_colorbar`.

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        Specify the figure within which to update the colorbars.

        If ``None``, use last active figure.

    Returns
    -------
    ypads_inches : ``numpy.ndarray``, shape ``(nrows-1, ncols)``
        2D numpy array of the distance in-between rows in inches.
    """
    fig = fig or plt.gcf()
    _, fig_height_inch = fig.get_size_inches()

    axs = get_sorted_axes_grid(fig)
    gridspec: GridSpec = axs[0, 0].get_subplotspec().get_gridspec()

    if gridspec.nrows == 1:
        raise ValueError("Only one row in 'fig'")

    ypads_inch = np.empty((gridspec.nrows-1, gridspec.ncols), dtype=Axes)
    for row in range(gridspec.nrows-1):
        for col in range(gridspec.ncols):
            bbox0 = axs[row, col].get_position()
            bbox1 = axs[row+1, col].get_position()
            ypads_inch[row, col] = (bbox0.y0 - bbox1.y1) * fig_height_inch

    return ypads_inch


def set_min_row_pads(
    ypads_pts: ArrayLike,
    fig: Optional[Figure] = None
) -> None:
    """
    Set the minimum distance between rows.

    Parameters
    ----------
    ypads_inches : ArrayLike
        The desired minimum distance in inches.

        You can pass a single float or number-of-rows floats.

    fig : ``matplotlib.figure.Figure``, optional
        Specify the figure within which to update the colorbars.

        If ``None``, use last active figure.
    """
    fig = fig or plt.gcf()
    _, fig_height_inch = fig.get_size_inches()

    axs = get_sorted_axes_grid(fig)
    gridspec: GridSpec = axs[0, 0].get_subplotspec().get_gridspec()
    if gridspec.ncols == 1:
        raise ValueError("Only one column in 'fig'")

    ypads_inches = np.array(ypads_pts) / PTS_PER_INCH
    if ypads_inches.size == 1:
        value = ypads_inches[0] if ypads_inches.shape else ypads_inches
        ypads_inches = np.full(gridspec.ncols-1, value)
    elif ypads_inches.shape != (gridspec.ncols-1,):
        msg = (
            f"{len(ypads_inches)=}, but it should be {gridspec.ncols-1}"
        )
        raise ValueError(msg)

    deltas = np.min(get_row_pads_inches(fig), axis=1) - ypads_inches
    for row in range(1, gridspec.nrows):
        for col in range(gridspec.ncols):
            bbox = axs[row, col].get_position()
            axs[row, col].set_position((
                bbox.x0,
                bbox.y0 + row*deltas[row-1] / fig_height_inch,
                bbox.width,
                bbox.height
            ))

    update_colorbars()


def get_figure_margins_inches(fig: Optional[Figure] = None) -> Edges:
    """
    Get margins of the figure.

    Only works if all axes of `fig` are part of one-and-the-same
    ``matplotlib.gridspec.GridSpec`` and if axes are aranged
    in a 2D grid.

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        Specify the figure within which to update the colorbars.

        If ``None``, use last active figure.

    Returns
    -------
    margins_inch : :class:`.Edges`
        left, right, top, and bottom margins of the figure.

        ``margins_inch.left``
            ``numpy.ndarray`` of all the `nrow` left margins

        ``margins_inch.right``
            ``numpy.ndarray`` of all the `nrow` right margins

        ``margins_inch.top``
            ``numpy.ndarray`` of all the `ncol` top margins

        ``margins_inch.bottom``
            ``numpy.ndarray`` of all the `ncol` bottom margins

    """
    fig = fig or plt.gcf()
    fw_inch, fh_inch = fig.get_size_inches()
    axs = get_sorted_axes_grid(fig)
    gridspec: GridSpec = axs[0, 0].get_subplotspec().get_gridspec()

    margins_inches = Edges(
        left=np.empty(gridspec.nrows, dtype=np.float64),
        right=np.empty(gridspec.nrows, dtype=np.float64),
        top=np.empty(gridspec.ncols, dtype=np.float64),
        bottom=np.empty(gridspec.ncols, dtype=np.float64)
    )

    for i, ax in enumerate(axs[:, 0]):
        margins_inches.left[i] = ax.get_position().x0 * fw_inch

    for i, ax in enumerate(axs[:, -1]):
        margins_inches.right[i] = (1.0 - ax.get_position().x1) * fw_inch

    for i, ax in enumerate(axs[0]):
        margins_inches.top[i] = (1.0 - ax.get_position().y1) * fh_inch

    for i, ax in enumerate(axs[-1]):
        margins_inches.bottom[i] = ax.get_position().y0 * fh_inch

    return margins_inches


def get_axes_position_inch(
    ax: Optional[Axes] = None
) -> Bbox:
    """
    Get bounding box of `ax` in inches.

    Wrapper function for ``matplotlib.axes.Axes.get_position()`` which converts
    it to inches.

    Parameters
    ----------
    ax : ``matplotlib.axes.Axes``, optional
        If ``None``, use last active axes.

    Returns
    -------
    bbox : ``matplotlib.transforms.Bbox``
        The bounding box of just the graph-area of `ax` in inches.

        Useful members:

        ``bbox.x0``/``bbox.x1``
            Location of the left/right edge in inches. Negative values are
            left of the figure left edge.

        ``bbox.y0``/``bbox.y1``
            Lower/upper edge in inches. Negative values are below the 
            figure bottom edge.

        ``bbox.width``/``bbox.height``
    """
    ax = ax or plt.gca()
    fig = ax.get_figure()
    if fig is None:
        raise ValueError("ax must be part of a figure")

    fw, fh = fig.get_size_inches()
    bbox = ax.get_position()

    return Bbox([[bbox.x0*fw, bbox.y0*fh], [bbox.x1*fw, bbox.y1*fh]])


def get_axes_tightbbox_inch(
    ax: Optional[Axes] = None,
    renderer: Optional[RendererBase] = None
) -> Bbox:
    """
    Get bounding box of `ax` including labels in inches.

    Wrapper function for ``matplotlib.axes.Axes.get_tightbbox()`` which converts
    it to inches.

    Parameters
    ----------
    ax : ``matplotlib.axes.Axes``, optional
        If ``None``, use last active axes.

    renderer : ``matplotlib.backend_bases.RendererBase``, optional
        The renderer used to draw the figure.

        Generally not necessary to pass it. If, however, you use
        a backend that takes a long time to render (e.g., a LuaLaTeX pgf
        backend), it may increase performance by passing the renderer.
        Use :func:`.get_renderer` to get your current renderer.

    Returns
    -------
    bbox : ``matplotlib.transforms.Bbox``
        The bounding box of `ax` including x/ylabels, titles, etc, in inches.

        Useful members:

        ``bbox.x0``/``bbox.x1``
            Location of the left/right edge in inches. Negative values are
            left of the figure left edge.

        ``bbox.y0``/``bbox.y1``
            Lower/upper edge in inches. Negative values are below the 
            figure bottom edge.

        ``bbox.width``/``bbox.height``
    """
    ax = ax or plt.gca()
    fig = ax.get_figure()
    if fig is None:
        raise ValueError("ax must be part of a figure")
    dpi = fig.get_dpi()

    tbbox_ax = ax.get_tightbbox(renderer)
    assert tbbox_ax
    xy_candidates = Edges([tbbox_ax.x0], [tbbox_ax.x1],
                          [tbbox_ax.y1], [tbbox_ax.y0])

    for cb in _colorbar_manager.colorbars:
        if cb.parent_ax is ax:
            tbbox_cb = cb.ax.get_tightbbox(renderer)
            assert tbbox_cb
            if cb.location == "left":
                xy_candidates.left.append(tbbox_cb.x0)
                xy_candidates.top.append(tbbox_cb.y1)
                xy_candidates.bottom.append(tbbox_cb.y0)
            if cb.location == "right":
                xy_candidates.right.append(tbbox_cb.x1)
                xy_candidates.top.append(tbbox_cb.y1)
                xy_candidates.bottom.append(tbbox_cb.y0)
            if cb.location == "top":
                xy_candidates.top.append(tbbox_cb.y1)
                xy_candidates.left.append(tbbox_cb.x0)
                xy_candidates.right.append(tbbox_cb.x1)
            if cb.location == "bottom":
                xy_candidates.bottom.append(tbbox_cb.y0)
                xy_candidates.left.append(tbbox_cb.x0)
                xy_candidates.right.append(tbbox_cb.x1)

    relevant_xy = (
        np.min([x0 / dpi for x0 in xy_candidates.left]),
        np.min([y0 / dpi for y0 in xy_candidates.bottom]),
        np.max([x1 / dpi for x1 in xy_candidates.right]),
        np.max([y1 / dpi for y1 in xy_candidates.top]),
    )

    rtn = Bbox.from_extents(*relevant_xy)
    return rtn


def make_me_nice(
    fig: Optional[Figure] = None,
    fix_figwidth: bool = True,
    margin_pad_pts: ArrayLike = 5.0,
    col_pad_pts: ArrayLike = 10.0,
    row_pad_pts: ArrayLike = 10.0,
    max_figwidth: float = np.inf,
    nruns: int = 2,
    renderer: Optional[RendererBase] = None,
) -> None:
    """
    Optimize whitespace in the figure.

    Re-arange axes in `fig` such that their margins don't overlap.
    Also change margins at the edges of the figure such that everything fits.
    Trim or expand the figure height accordingly.

    Advantages over ``matplotlib.pyplot.tight_layout`` or 
    `constrained layout <https://matplotlib.org/stable/users/explain/axes/constrainedlayout_guide.html>`_:

    - Keeps widths constant (either of the axes, or of the figure)
    - Handle colorbars as one may expect (if they were added using
      :func:`.add_colorbar`)
    - Updates figure height to optimize white-space for fixed aspect ratios

    Disadvantages:

    - Can only handle `nrows` times `ncols` grids. If you have anything fancy
      (an axes that spans multiple columns), you cannot use this
      straightforwardly.

    Parameters
    ----------
    fig : ``matplotlib.figure.Figure``, optional
        If ``None``, use last active figure.

    fix_figwidth : bool, default ``True``
        Configure if the figure width is kept constant or not.

        ``True``:
            Keep the figure width constant and scale all axes-widths
            accordingly.
        ``False``:
            Keep axes widths constant and scale figure width accordingly. 
            Also note `fail_if_figwidth_exceeds` parameter.

    margin_pad_pts : ArrayLike, default ``5.0``
        Extra padding for the figure edges in pts.

        float:
            Same padding for left, right, top, bottom edge.
        (float, float, float, float):
            Different padding for left, right, top, bottom edge.

    col_pad_pts, row_pad_pts : ArrayLike, default ``10.0``
        Extra padding between the columns (rows) in pts.

        float:
            Same padding in-between all columns (rows).
        (float, ...):
            Different values in-between all columns. Must have a length
            of ``number_of_columns-1`` (``number_of_rows-1``).

    max_figwidth : float, default ``numpy.inf``
        Only relevant if ``fix_figwidth == False``.

        Maximum figure width in inches. Throws 
        :class:`.FigureWidthTooLargeError` if the new figure width exceeds
        this value.

    nruns : int, default ``2``
        Number of times the algorithm runs.

        If your axes change significantly in size, different ticklabels may
        be drawn which may change the size of the axes. To account for this,
        ``make_me_nice`` has to run another time.

        If the margins produced by ``make_me_nice`` are wrong, increasing
        the number of runs may help.

    renderer : ``matplotlib.backend_bases.RendererBase``, optional
        The renderer used to draw the figure.

        Generally not necessary to pass it. If, however, you use
        a backend that takes a long time to render (e.g., a LuaLaTeX pgf
        backend), it may increase performance by passing the renderer.
        Use :func:`.get_renderer` to get your current renderer.

    Notes
    -----
    - Cannot handle fancy GridSpecs, e.g., where one
      subplot spans multiple other subplots.
      If you need one of those, you're on your own.

    - If you have subplots with different aspect ratios and `fig_width` is not
      ``None``, the positioning of the subplots may be incorrect (e.g.,
      off-centered in the column). Use :func:`.align_axes_vertically` or
      :func:`.align_axes_horizontally` to fix that.

    - If you use a different backend in `plt.savefig` than the default,
      you need to specify that before creating the figure. E.g., with
      ``matplotlib.use("some-backend")``.
    """
    fig = fig or plt.gcf()
    fw_inch, fh_inch = fig.get_size_inches()
    axs = get_sorted_axes_grid(fig)
    gridspec: GridSpec = axs[0, 0].get_subplotspec().get_gridspec()
    nrows, ncols = gridspec.nrows, gridspec.ncols
    renderer = renderer or get_renderer(fig)

    margin_pad_pts = np.array(margin_pad_pts)
    if margin_pad_pts.size == 1:
        value = margin_pad_pts[0] if margin_pad_pts.shape else margin_pad_pts
        margin_pad_pts = np.array([value] * 4)
    elif margin_pad_pts.shape != (4,):
        raise ValueError(f"{margin_pad_pts.shape=} is invalid")
    mpads_inch = Edges(*(margin_pad_pts / PTS_PER_INCH))

    if ncols > 1:
        col_pad_pts = np.array(col_pad_pts)
        if col_pad_pts.size == 1:
            value = col_pad_pts[0] if col_pad_pts.shape else col_pad_pts
            col_pad_pts = np.array([value] * (ncols-1))
        elif col_pad_pts.shape != (ncols-1,):
            raise ValueError(f"{col_pad_pts.shape=} is invalid")
        col_pads_inch = col_pad_pts / PTS_PER_INCH
    else:
        col_pads_inch = np.array([0.0])

    if nrows > 1:
        row_pad_pts = np.array(row_pad_pts)
        if row_pad_pts.size == 1:
            value = row_pad_pts[0] if row_pad_pts.shape else row_pad_pts
            row_pad_pts = np.array([value] * (nrows-1))
        elif row_pad_pts.shape != (ncols-1,):
            raise ValueError(f"{row_pad_pts.shape=} is invalid")
        row_pads_inch = row_pad_pts / PTS_PER_INCH
    else:
        row_pads_inch = np.array([0.0])

    bboxes_inch = np.empty((nrows, ncols), dtype=Bbox)
    tbboxes_inch = np.empty((nrows, ncols), dtype=Bbox)

    for row in range(nrows):
        for col in range(ncols):
            bboxes_inch[row, col] = get_axes_position_inch(axs[row, col])
            tbboxes_inch[row, col] = get_axes_tightbbox_inch(
                axs[row, col], renderer=renderer)

    extra_wspaces_inch = np.zeros(ncols)
    extra_wspaces_inch[0] = np.min([t.x0 for t in tbboxes_inch[:, 0]])
    for col in range(1, ncols):
        extra_wspaces_inch[col] = (
            np.min([t.x0 for t in tbboxes_inch[:, col]])
            - np.max([t.x1 for t in tbboxes_inch[:, col-1]]))

    extra_hspaces_inch = np.zeros(nrows)
    extra_hspaces_inch[0] = fh_inch - np.max([t.y1 for t in tbboxes_inch[0]])
    for row in range(1, nrows):
        extra_hspaces_inch[row] = (
            np.min([t.y0 for t in tbboxes_inch[row-1]])
            - np.max([t.y1 for t in tbboxes_inch[row]]))

    new_fw_inch: float = (
        (np.max([t.x1 for t in tbboxes_inch[:, -1]])
         - np.min([t.x0 for t in tbboxes_inch[:, 0]]))
        - np.sum(extra_wspaces_inch[1:])
        + mpads_inch.left + mpads_inch.right
        + np.sum(col_pads_inch)
    )

    if fix_figwidth:
        scale = fw_inch / new_fw_inch

        for row in range(nrows):
            for col in range(ncols):
                set_axes_size(bboxes_inch[row, col].width * scale,
                              bboxes_inch[row, col].height * scale,
                              ax=axs[row, col],
                              anchor="center")
                tbboxes_inch[row, col] = get_axes_tightbbox_inch(
                    axs[row, col], renderer=renderer)

        if nruns > 1:
            next_fix_figwidth = True
        else:
            next_fix_figwidth = False

        return make_me_nice(
            fig=fig,
            fix_figwidth=next_fix_figwidth,
            max_figwidth=np.inf,
            margin_pad_pts=margin_pad_pts,
            row_pad_pts=row_pad_pts,
            col_pad_pts=col_pad_pts,
            nruns=nruns-1,
            renderer=renderer
        )

    if new_fw_inch > max_figwidth:
        raise FigureWidthTooLargeError

    new_fh_inch = (
        (np.max([t.y1 for t in tbboxes_inch[0]])
            - np.min([t.y0 for t in tbboxes_inch[-1]]))
        - np.sum(extra_hspaces_inch[1:])
        + mpads_inch.top + mpads_inch.bottom
        + np.sum(row_pads_inch)
    )

    fig.set_size_inches(new_fw_inch, new_fh_inch)

    for row in range(nrows):
        for col in range(ncols):
            x0s_inch = (
                bboxes_inch[row, col].x0
                - np.sum(extra_wspaces_inch[:col+1])
                + np.sum(col_pads_inch[:col])
                + mpads_inch.left
            )
            y0s_inch = (
                bboxes_inch[row, col].y0
                + np.sum(extra_hspaces_inch[:row+1])
                - np.sum(row_pads_inch[:row])
            ) - fh_inch + new_fh_inch - mpads_inch.top

            axs[row, col].set_position((
                x0s_inch / new_fw_inch,
                y0s_inch / new_fh_inch,
                bboxes_inch[row, col].width / new_fw_inch,
                bboxes_inch[row, col].height / new_fh_inch,
            ))

    update_colorbars()


def align_axes_vertically(
    ax: Axes,
    reference_ax: Axes,
    alignment: Literal["center", "top", "bottom"] = "center",
) -> None:
    """
    Set horizontal position of `ax` relative to `reference_ax`.

    Parameters
    ----------
    ax : ``matplotlib.axes.Axes``
        Axes to reposition.

    reference_ax : ``matplotlib.axes.Axes``
        Reference axes.

    alignment : {``"center"``, ``"top"``, ``"bottom"``}, default ``"center"``
        Which reference point to take from `reference_ax`.
    """
    bbox_ax = ax.get_position()
    bbox_ref = reference_ax.get_position()

    if alignment == "center":
        delta = bbox_ref.height - bbox_ax.height
        y0 = bbox_ref.y0 + delta / 2.0
    elif alignment == "top":
        y0 = bbox_ref.y1 - bbox_ax.height
    elif alignment == "bottom":
        y0 = bbox_ref.y0
    else:
        valid_anchors = "left", "top", "bottom"
        msg = f"{alignment=}, but it should be one of {valid_anchors}"
        raise ValueError(msg)
    ax.set_position((bbox_ax.x0, y0, bbox_ax.width, bbox_ax.height))
    update_colorbars()


def align_axes_horizontally(
    ax: Axes,
    reference_ax: Axes,
    alignment: Literal["center", "left", "right"] = "center"
) -> None:
    """
    Set horizontal position of `ax` relative to `reference_ax`.

    Parameters
    ----------
    ax : ``matplotlib.axes.Axes``
        Axes to reposition.

    reference_ax : ``matplotlib.axes.Axes``
        Reference axes.

    alignment : {``"center"``, ``"left"``, ``"right"``}, default ``"center"``
        Which reference point to take from `reference_ax`.
    """
    bbox_ax = ax.get_position()
    bbox_ref = reference_ax.get_position()

    if alignment == "center":
        delta = bbox_ref.width - bbox_ax.width
        x0 = bbox_ref.x0 + delta / 2.0
    elif alignment == "left":
        x0 = bbox_ref.x1 - bbox_ax.width
    elif alignment == "right":
        x0 = bbox_ref.x0
    else:
        valid_anchors = "left", "top", "bottom"
        msg = f"{alignment=}, but it should be one of {valid_anchors}"
        raise ValueError(msg)
    ax.set_position((x0, bbox_ax.y0, bbox_ax.width, bbox_ax.height))
    update_colorbars()


def get_axes_margins_inches(
        ax: Optional[Axes] = None,
        renderer: Optional[RendererBase] = None
) -> Edges:
    """
    Get left, right, top, bottom margins of `ax`.

    Parameters
    ----------
    ax : ``matplotlib.axes.Axes``, optional
        If ``None``, use last active axes.

    renderer : ``matplotlib.backend_bases.RendererBase``, optional
        The renderer used to draw the figure.

        Generally not necessary to pass it. If, however, you use
        a backend that takes a long time to render (e.g., a LuaLaTeX pgf
        backend), it may increase performance by passing the renderer.
        Use :func:`.get_renderer` to get your current renderer.

    Returns
    -------
    margins : :class:`.Edges`
        The margins in inches wrapped in an instance of :class:`.Edges`,
        e.g., ``margins.left`` is the left margin.
    """
    tbbox = get_axes_tightbbox_inch(ax, renderer)
    bbox = get_axes_position_inch(ax)
    return Edges(
        bbox.x0 - tbbox.x0,
        tbbox.x1 - bbox.x1,
        tbbox.y1 - bbox.y1,
        bbox.y0 - tbbox.y0
    )


if __name__ == "__main__":
    print("oi mate")
