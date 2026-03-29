# Orbital Observatory

An interactive gravitational simulator built in Python.
Select real celestial objects, place them in a custom solar system, and watch the physics unfold.

![demo gif — solar system overview](assets/simulation.gif)

---

## What it does

- **Real astrophysical catalogue** — solar system planets, moons, asteroids, comets, and exoplanets (TRAPPIST-1e, WASP-12b, Kepler-16b…) with real masses and physical radii from NASA/JPL data
- **Live orbital mechanics** — every variable (orbital velocity, period, gravitational force, specific energy, Hill sphere, Roche limit…) is computed analytically in real time as you move the distance slider
- **Configurable star** — change the star's mass and radius; the habitable zone, Roche limit, orbital velocities, and spectral classification all update instantly
- **N-body chaos** — add multiple objects from the catalogue; they all interact gravitationally with each other, not just with the star
- **Realistic collisions** — bodies merge on contact using momentum conservation; the survivor inherits the combined mass, volume-averaged radius, and blended colour

![demo gif — collision chain](assets/collision.gif)

---

## Physics implementation

### Integration method
The simulation uses **Velocity Verlet** integration, chosen over simple Euler because it conserves energy over long time scales:

```
x(t+dt) = x(t) + v(t)·dt + ½·a(t)·dt²
v(t+dt) = v(t) + ½·[a(t) + a(t+dt)]·dt
```

Timestep is 8 hours per frame, adjustable from 1h to 512h via `+`/`-`.

### Gravitational N-body
All pairwise gravitational forces are computed each step:

```
F_ij = G · m_i · m_j / r_ij²   (directed along r_ij)
```

Softening uses the sum of physical radii as a minimum distance, preventing singularities when bodies overlap before the collision detector fires.

### Orbital variables (all analytic)

| Variable | Formula |
|---|---|
| Orbital velocity | `v = √(GM★/r)` |
| Escape velocity | `v_esc = √(2GM★/r)` |
| Orbital period (Kepler III) | `T = 2π√(r³/GM★)` |
| Gravitational force | `F = GM★m/r²` |
| Specific orbital energy | `E = -GM★/(2r)` |
| Hill sphere | `r_H = r·(m/3M★)^(1/3)` |
| Roche limit | `d = 2.44·R★·(ρ★/ρ_obj)^(1/3)` |
| Habitable zone | scales as `√(L/L☉)`, with `L ∝ M★^3.5` |

### Collision model
Collisions use **perfectly inelastic momentum conservation**:

```
v_merger = (m₁·v₁ + m₂·v₂) / (m₁ + m₂)
R_merger = (R₁³ + R₂³)^(1/3)   (volume conservation)
```

If the post-collision velocity would exceed escape velocity (i.e. the collision would eject the merged body), it is clamped to 92% of `v_esc` in the tangential direction. This is a simplification: in reality the outcome depends on impact angle and relative velocity.

---

## Known limitations and simplifications

**2D only** — real orbital mechanics is 3D; inclinations, eccentricities, and out-of-plane dynamics are not modelled. All orbits are initialised as circular and co-planar.

**Point-mass gravity** — bodies are treated as point masses for gravitational purposes. The physical radii are only used for collision detection and Roche limit calculations.

**Fixed timestep** — the 8-hour timestep is a compromise. Close encounters (e.g. a small body passing near Jupiter) can be under-resolved at high time multipliers, leading to artificial energy gain. A real simulator would use adaptive timestep.

**Inelastic collision model** — real planetary collisions are highly complex (partial accretion, debris fields, ejecta). This simulation uses a simplified perfect merger. The post-collision velocity clamp is a numerical stabilisation, not derived from first principles.

**Star is fixed** — the star does not move in response to gravitational forces from planets (infinite mass approximation). This is accurate for mass ratios M★/m_planet > 1000 but breaks down for equal-mass binary systems.

**Habitable zone is a rough estimate** — the HZ boundaries use a simple luminosity scaling (`L ∝ M^3.5`) valid only for main-sequence stars. It does not account for atmospheric composition, albedo, or stellar activity.

---

## Stack

```
Python 3.11+
pygame 2.5      — rendering, game loop, input
numpy           — vectorised physics computations
```

No external physics engine — all mechanics implemented from scratch.

---

## Run

```bash
pip install pygame numpy
python simulation.py
```

## Controls

| Input | Action |
|---|---|
| Click catalogue | Add object to simulation |
| Right-click body | Remove body |
| Click body | Select — shows live variables |
| Distance slider | Move selected object, all vars update |
| Star mass / radius | Rescale the star, HZ, and all orbits |
| `+` / `-` | Time multiplier (0.125× → 64×) |
| `C` | Clear all added objects |
| `S` | Reset star to Sun |
| `R` | Full reset |
| `V` / `F` | Velocity / force vectors |
| `H` | Toggle habitable zone ring |
| `SPACE` | Pause / resume |

## Project structure

```
simulation_orbital_game/
├── simulation.py   
├── catalogue.py    # astrophysical data (masses, radii, colours, descriptions)
└── README.md
```


- **Adaptive timestep** — reduce dt automatically during close encounters
- **Export to GIF/MP4** — record simulations directly
- **Orbital elements display** — semi-major axis, eccentricity, inclination computed from live state vectors
- **Scenario presets** — TRAPPIST-1 system, Kepler-16 circumbinary, asteroid belt
