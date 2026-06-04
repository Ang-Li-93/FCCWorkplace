# Geometry: ALLEGRO silicon wrapper

## TL;DR — a sensitive silicon wrapper already exists in ALLEGRO

You do **not** need to build a new detector for the first milestone. ALLEGRO
`o1_v03` already includes a sensitive silicon-wrapper **barrel** and **disks**
outside the gaseous drift chamber, and they produce `edm4hep::SimTrackerHit`
collections.

| property | value | source |
|---|---|---|
| barrel detector | `SiWrB` (system id 23) | `SiliconWrapper_o1_v03.xml` |
| barrel collection | **`SiWrBCollection`** | readout name |
| disk detector / collection | `SiWrD` / `SiWrDCollection` (id 24) | same |
| inner-layer radius | **2040 mm** | `DectDimensions.xml` |
| second layer radius | 2060 mm (= r1 + 2 cm) | wrapper XML |
| outer radius / half length | 2080 mm / **2400 mm** | `DectDimensions.xml` |
| sensitive thickness | **50 µm** (`SiWr_Sensitive_Thickness = 5e-2 mm`) | wrapper XML |
| material | Silicon (ATLASPix3-like module) | wrapper XML |
| cellID encoding | `system:5,side:-2,layer:3,module:16,sensor:6` | `GlobalTrackerReadoutID` |

The wrapper is the symlinked IDEA silicon wrapper:
`FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/SiliconWrapper_o1_v03.xml`
→ `FCCee/IDEA/compact/IDEA_o1_v03/SiliconWrapper_o1_v03.xml`.

### Key consequence for PixESL: there is **no pixel segmentation**
The readout cellID resolves down to `sensor` (a ~20×19 mm ATLASPix3 tile), **not
to a 20 µm pixel**. So for the first version we *pixelize in the converter*
(`conversion/convert_simhits_to_pixesl.py`) from the SimTrackerHit global
position. This is exactly the WP1 plan. Real cellID decoding comes later (below).

## Discover / inspect the geometry yourself

```bash
source setup/setup_key4hep.sh
bash geometry/find_allegro_geometry.sh        # -> outputs/allegro_geometry_search.txt
bash geometry/inspect_allegro_geometry.sh     # auto-picks latest ALLEGRO XML
# or point at a specific file:
bash geometry/inspect_allegro_geometry.sh \
     $K4GEO/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml
```

## Editing geometry in your **local k4geo fork**

Your fork: `git@github.com:Ang-Li-93/k4geo.git`. Clone + wire it:

```bash
bash setup/clone_local_forks.sh                 # clones to /gpfs/.../Allegro
export LOCAL_K4GEO=/gpfs/mnt/gpfs01/usfcc/ali3/Allegro/k4geo   # dir containing FCCee/
source setup/setup_key4hep.sh                   # now $K4GEO points at your fork
```

`k4geo` is pure geometry XML — no compilation needed, edit and re-run `ddsim`.

### Recommended improvement: add a real 20 µm pixel segmentation to SiWrB
In your local fork, edit the silicon-wrapper readout so the cellID encodes
pixels. In `SiliconWrapper_o1_v03.xml` change the `SiWrBCollection` readout from:

```xml
<readout name="SiWrBCollection">
    <id>${GlobalTrackerReadoutID}</id>
</readout>
```

to something like:

```xml
<readout name="SiWrBCollection">
    <segmentation type="CartesianGridXY" grid_size_x="0.02*mm" grid_size_y="0.02*mm"/>
    <id>system:5,side:-2,layer:3,module:16,sensor:6,x:24:-12,y:-12</id>
</readout>
```

After this, `SimTrackerHit::getCellID()` encodes the pixel indices and the
converter can decode pixels directly instead of mapping from position. (Adjust
the bit widths to your needs; the local-x/local-y fields must be wide enough for
the module size / 20 µm.)

## Standalone MAPS wrapper template

`MAPSWrapper_o1_v00.xml` is an **optional template** for a standalone simplified
MAPS barrel layer with a `CartesianGridXY` 20 µm readout
(`MAPSWrapperReadout` → collection listed as `MAPSWrapperBarrelHits` fallback in
`conversion/collections_config.yaml`). Its `<readout>`/segmentation block is
correct and reusable; the `<detector>` block is a commented skeleton because the
exact barrel detector `type=` schema depends on your k4geo version. To use it,
add `<include ref="../../../../<path>/MAPSWrapper_o1_v00.xml"/>` to the ALLEGRO
compact XML (in your local fork) and fill in a valid barrel detector type.

For the first milestone, prefer the existing `SiWrBCollection` over this template.
