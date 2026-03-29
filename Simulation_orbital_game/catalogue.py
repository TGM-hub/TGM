"""
catalogue.py — Real astrophysical data for the sandbox.

All masses in kg, distances in AU (converted to metres in sim),
orbital velocities in m/s. Sources: NASA fact sheets, JPL Horizons,
NASA Exoplanet Archive.
"""

AU = 1.496e11   # metres per AU
M_SUN = 1.989e30

# ─────────────────────────────────────────────────────────────
#  CATALOGUE ENTRY FORMAT
#  {
#    "name":        str,
#    "category":    str,          # for sidebar grouping
#    "mass":        float,        # kg
#    "radius_px":   int,          # display radius in pixels
#    "color":       (r, g, b),
#    "description": str,
#    # Optional placement hint (AU from Sun along +X axis):
#    "default_dist_au": float,    # where to drop if not dragged
#    "default_vel_ms":  float,    # tangential orbital velocity m/s (+ = CCW)
#  }
# ─────────────────────────────────────────────────────────────

CATALOGUE = {

    # ── SOLAR SYSTEM PLANETS ─────────────────────────────────
    "Mercury": {
        "category": "Solar System",
        "mass": 3.285e23,
        "radius_px": 4,
        "color": (180, 140, 110),
        "description": "Smallest planet. Eccentric orbit, no atmosphere.",
        "default_dist_au": 0.387,
        "default_vel_ms": 47400,
    },
    "Venus": {
        "category": "Solar System",
        "mass": 4.867e24,
        "radius_px": 7,
        "color": (220, 185, 100),
        "description": "Hottest planet. Retrograde rotation, thick CO₂ atmosphere.",
        "default_dist_au": 0.723,
        "default_vel_ms": 35020,
    },
    "Earth": {
        "category": "Solar System",
        "mass": 5.972e24,
        "radius_px": 8,
        "color": (80, 160, 220),
        "description": "Our home. 1 AU from the Sun.",
        "default_dist_au": 1.000,
        "default_vel_ms": 29780,
    },
    "Moon": {
        "category": "Solar System",
        "mass": 7.342e22,
        "radius_px": 3,
        "color": (200, 200, 195),
        "description": "Earth's natural satellite. ~384 400 km from Earth.",
        "default_dist_au": 1.003,   # ~Earth + 384 400 km
        "default_vel_ms": 30800,    # Earth orbital + lunar orbital (~1022 m/s tangential)
    },
    "Mars": {
        "category": "Solar System",
        "mass": 6.390e23,
        "radius_px": 5,
        "color": (200, 80, 50),
        "description": "The Red Planet. Two tiny moons: Phobos & Deimos.",
        "default_dist_au": 1.524,
        "default_vel_ms": 24100,
    },
    "Jupiter": {
        "category": "Solar System",
        "mass": 1.898e27,
        "radius_px": 14,
        "color": (220, 180, 140),
        "description": "Largest planet. Great Red Spot. 95 known moons.",
        "default_dist_au": 5.203,
        "default_vel_ms": 13070,
    },
    "Saturn": {
        "category": "Solar System",
        "mass": 5.683e26,
        "radius_px": 12,
        "color": (235, 215, 155),
        "description": "Ring system visible from Earth. Density less than water.",
        "default_dist_au": 9.537,
        "default_vel_ms": 9690,
    },
    "Uranus": {
        "category": "Solar System",
        "mass": 8.681e25,
        "radius_px": 10,
        "color": (140, 220, 230),
        "description": "Rotates on its side (98° axial tilt).",
        "default_dist_au": 19.19,
        "default_vel_ms": 6800,
    },
    "Neptune": {
        "category": "Solar System",
        "mass": 1.024e26,
        "radius_px": 10,
        "color": (60, 90, 220),
        "description": "Strongest winds in the solar system (~2 100 km/h).",
        "default_dist_au": 30.07,
        "default_vel_ms": 5430,
    },
    "Pluto": {
        "category": "Solar System",
        "mass": 1.303e22,
        "radius_px": 3,
        "color": (210, 180, 160),
        "description": "Dwarf planet. Highly elliptical orbit (17° inclined).",
        "default_dist_au": 39.48,
        "default_vel_ms": 4740,
    },

    # ── MOONS ────────────────────────────────────────────────
    "Ganymede": {
        "category": "Moons",
        "mass": 1.482e23,
        "radius_px": 5,
        "color": (170, 155, 140),
        "description": "Jupiter's moon. Largest moon in the solar system.",
        "default_dist_au": 5.207,
        "default_vel_ms": 13200,
    },
    "Titan": {
        "category": "Moons",
        "mass": 1.345e23,
        "radius_px": 5,
        "color": (210, 170, 90),
        "description": "Saturn's moon. Thick nitrogen atmosphere, methane lakes.",
        "default_dist_au": 9.545,
        "default_vel_ms": 9730,
    },
    "Europa": {
        "category": "Moons",
        "mass": 4.800e22,
        "radius_px": 4,
        "color": (230, 210, 190),
        "description": "Jupiter's moon. Subsurface ocean — prime candidate for life.",
        "default_dist_au": 5.204,
        "default_vel_ms": 13100,
    },
    "Io": {
        "category": "Moons",
        "mass": 8.932e22,
        "radius_px": 4,
        "color": (240, 200, 80),
        "description": "Jupiter's moon. Most volcanically active body in solar system.",
        "default_dist_au": 5.203,
        "default_vel_ms": 13070,
    },

    # ── ASTEROIDS & COMETS ───────────────────────────────────
    "Ceres": {
        "category": "Asteroids & Comets",
        "mass": 9.393e20,
        "radius_px": 3,
        "color": (160, 150, 140),
        "description": "Largest asteroid / dwarf planet in the asteroid belt.",
        "default_dist_au": 2.77,
        "default_vel_ms": 17900,
    },
    "Vesta": {
        "category": "Asteroids & Comets",
        "mass": 2.590e20,
        "radius_px": 2,
        "color": (140, 130, 120),
        "description": "Second-largest asteroid. Visited by Dawn spacecraft.",
        "default_dist_au": 2.36,
        "default_vel_ms": 19340,
    },
    "Halley's Comet": {
        "category": "Asteroids & Comets",
        "mass": 2.200e14,
        "radius_px": 2,
        "color": (180, 220, 255),
        "description": "Famous short-period comet. Returns every ~75 years.",
        "default_dist_au": 1.0,
        "default_vel_ms": 54000,  # near perihelion
    },
    "Apophis": {
        "category": "Asteroids & Comets",
        "mass": 6.100e10,
        "radius_px": 2,
        "color": (160, 140, 100),
        "description": "Near-Earth asteroid. Close approach in 2029.",
        "default_dist_au": 0.92,
        "default_vel_ms": 30700,
    },
    "67P/Churyumov": {
        "category": "Asteroids & Comets",
        "mass": 9.982e12,
        "radius_px": 2,
        "color": (100, 100, 90),
        "description": "Rosetta mission target. Duck-shaped nucleus.",
        "default_dist_au": 1.24,
        "default_vel_ms": 34000,
    },

    # ── EXOPLANETS ───────────────────────────────────────────
    "TRAPPIST-1e": {
        "category": "Exoplanets",
        "mass": 4.156e24,  # 0.696 Earth masses
        "radius_px": 7,
        "color": (180, 100, 60),
        "description": "Potentially habitable. In TRAPPIST-1 HZ. 40 ly away.",
        "default_dist_au": 0.93,
        "default_vel_ms": 30000,
    },
    "Kepler-442b": {
        "category": "Exoplanets",
        "mass": 1.790e25,  # ~3 Earth masses estimate
        "radius_px": 9,
        "color": (100, 180, 130),
        "description": "Super-Earth in habitable zone. ESI = 0.84.",
        "default_dist_au": 1.19,
        "default_vel_ms": 27300,
    },
    "Hot Jupiter (51 Peg b)": {
        "category": "Exoplanets",
        "mass": 8.940e26,  # ~0.47 Jupiter masses
        "radius_px": 13,
        "color": (220, 120, 50),
        "description": "First exoplanet found around Sun-like star. Ultra-close orbit.",
        "default_dist_au": 0.052,
        "default_vel_ms": 130000,
    },
    "Proxima b": {
        "category": "Exoplanets",
        "mass": 7.966e24,  # ~1.27 Earth masses
        "radius_px": 8,
        "color": (200, 80, 80),
        "description": "Nearest exoplanet to Earth. Orbits Proxima Centauri.",
        "default_dist_au": 0.049,
        "default_vel_ms": 134000,
    },
    "GJ 1214 b": {
        "category": "Exoplanets",
        "mass": 3.835e25,  # ~6.55 Earth masses
        "radius_px": 9,
        "color": (80, 140, 200),
        "description": "Super-Earth / water world candidate. Dense steam atmosphere.",
        "default_dist_au": 0.014,
        "default_vel_ms": 250000,
    },
    "HD 209458 b": {
        "category": "Exoplanets",
        "mass": 1.310e27,  # ~0.69 Jupiter masses
        "radius_px": 13,
        "color": (240, 160, 60),
        "description": "Osiris — first exoplanet with detected atmosphere. Evaporating.",
        "default_dist_au": 0.047,
        "default_vel_ms": 137000,
    },
    "WASP-12b": {
        "category": "Exoplanets",
        "mass": 2.640e27,  # ~1.39 Jupiter masses
        "radius_px": 14,
        "color": (255, 80, 30),
        "description": "Ultra-hot Jupiter. Being torn apart by its star. T=2600K.",
        "default_dist_au": 0.023,
        "default_vel_ms": 200000,
    },
    "Kepler-16b": {
        "category": "Exoplanets",
        "mass": 1.072e26,  # ~0.333 Jupiter masses
        "radius_px": 10,
        "color": (160, 120, 200),
        "description": "Circumbinary planet — orbits TWO stars (Tatooine-like!).",
        "default_dist_au": 0.705,
        "default_vel_ms": 35400,
    },
}

# Ordered category list for sidebar display
CATEGORIES = [
    "Solar System",
    "Moons",
    "Asteroids & Comets",
    "Exoplanets",
]

def get_by_category(category):
    return {k: v for k, v in CATALOGUE.items() if v["category"] == category}