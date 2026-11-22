import * as pmtiles from "https://esm.sh/pmtiles@4.4.1";

const PMTILES_URL = "https://mapping-vt-tiles.s3.amazonaws.com/vermont.pmtiles";
const SANBORN_TILES = "https://mapping-vt-tiles.s3.amazonaws.com/sanborn/{z}/{x}/{y}.png";
const CENSUS_URL = "data/census_1900.geojson";
const ADULT_OVER = 16;

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const hadHashOnLoad = Boolean(window.location.hash); // read before the map writes its own

const isMobile = () => window.matchMedia("(max-width: 768px)").matches;

function mapPadding() {
	if (isMobile()) {
		return { top: 56, right: 30, bottom: window.innerHeight * 0.62 + 20, left: 30 };
	}
	const panelWidth = document.getElementById("panel").offsetWidth;
	return { top: 60, right: 40, bottom: 40, left: panelWidth + 40 };
}

const map = new maplibregl.Map({
	container: "map",
	style: {
		version: 8,
		glyphs: "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf",
		sprite: "https://protomaps.github.io/basemaps-assets/sprites/v4/light",
		sources: {
			protomaps: {
				type: "vector",
				url: `pmtiles://${PMTILES_URL}`,
				attribution: '<a href="https://protomaps.com">Protomaps</a> © <a href="https://openstreetmap.org">OpenStreetMap</a>',
			},
			sanborn: {
				type: "raster",
				tiles: [SANBORN_TILES],
				tileSize: 256,
				minzoom: 14,
				maxzoom: 21,
				attribution: 'Sanborn Map Co. 1896, <a href="https://www.loc.gov/collections/sanborn-maps/">Library of Congress</a>',
			},
		},
		layers: [
			...basemaps.layers("protomaps", basemaps.namedFlavor("light"), { lang: "en" }),
			{
				id: "sanborn",
				type: "raster",
				source: "sanborn",
				paint: { "raster-opacity": 0.85, "raster-fade-duration": 150 },
			},
		],
	},
	center: [-72.4441, 43.1338],
	zoom: 16.5,
	maxZoom: 21,
	hash: true,
	attributionControl: false,
});

map.addControl(new maplibregl.NavigationControl(), "top-right");
map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

// MapLibre expands the compact attribution once its sources report attribution text.
// Collapse it the first time that happens; the ⓘ button still opens it.
const attrib = map.getContainer().querySelector(".maplibregl-ctrl-attrib");
function collapseAttribution() {
	if (!attrib.classList.contains("maplibregl-compact")) return;
	attrib.classList.remove("maplibregl-compact-show");
	map.off("styledata", collapseAttribution);
	map.off("sourcedata", collapseAttribution);
}
map.on("styledata", collapseAttribution);
map.on("sourcedata", collapseAttribution);

let houses = [];
let selected = null;
const markers = new Map(); // address -> { marker, el }

const flagsOf = (props) => props.top_birth;
const flagString = (props) => flagsOf(props).map((c) => c.flag).join("") || "🏠";
const flagTitle = (props) => flagsOf(props).map((c) => c.country).join(" / ");

function escapeHtml(s) {
	return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// --- Markers ---

function buildMarkers() {
	houses.forEach((f) => {
		// MapLibre positions markers by setting `transform` on this outer element every frame,
		// so it must stay unstyled. The visible pill (with its hover/selected scaling) is a child.
		const el = document.createElement("div");
		el.className = "house-marker-anchor";
		const pill = document.createElement("div");
		pill.className = "house-marker";
		el.appendChild(pill);
		el.addEventListener("click", (e) => {
			e.stopPropagation();
			selectHouse(f.properties.address);
		});
		const marker = new maplibregl.Marker({ element: el, anchor: "center" })
			.setLngLat(f.geometry.coordinates)
			.addTo(map);
		markers.set(f.properties.address, { marker, el, pill });
	});
	refreshMarkers();
}

function refreshMarkers() {
	houses.forEach((f) => {
		const { el, pill } = markers.get(f.properties.address);
		const isSelected = f.properties.address === selected;
		pill.textContent = flagString(f.properties);
		pill.title = `${f.properties.address}: ${flagTitle(f.properties)}`;
		pill.classList.toggle("selected", isSelected);
		el.classList.toggle("selected", isSelected); // lifts it above neighbouring pins
	});
}

// --- List ---

function streetOf(f) {
	return f.properties.street === "Square" ? "The Square" : `${f.properties.street} Street`;
}

function renderList() {
	const list = document.getElementById("house-list");
	list.innerHTML = "";
	const byStreet = {};
	houses.forEach((f) => (byStreet[streetOf(f)] ??= []).push(f));
	Object.keys(byStreet)
		.sort()
		.forEach((street) => {
			const h = document.createElement("div");
			h.className = "street-heading";
			h.textContent = street;
			list.appendChild(h);
			byStreet[street]
				.sort((a, b) => Number(a.properties.house_num) - Number(b.properties.house_num))
				.forEach((f) => {
					const p = f.properties;
					const row = document.createElement("div");
					row.className = "house-row";
					row.dataset.address = p.address;
					row.innerHTML = `
						<div class="flags" title="${escapeHtml(flagTitle(p))}">${flagString(p)}</div>
						<div>
							<div class="addr">${escapeHtml(p.address)}</div>
							<div class="sub">${p.people} ${p.people === 1 ? "person" : "people"} · ${p.adults} over ${ADULT_OVER}</div>
						</div>`;
					row.addEventListener("click", () => selectHouse(p.address));
					list.appendChild(row);
				});
		});
	const note = document.createElement("div");
	note.className = "list-note";
	note.textContent =
		"Three households with no house number written on the census page aren't on the map yet.";
	list.appendChild(note);
	markActiveRow();
}

function markActiveRow() {
	document.querySelectorAll(".house-row").forEach((row) => {
		row.classList.toggle("active", row.dataset.address === selected);
	});
}

// --- Detail ---

// Count residents over 16 by birth country, most common first.
function tally(props) {
	const counts = {};
	props.residents
		.filter((r) => r.adult && r.birth_country)
		.forEach((r) => {
			counts[r.birth_country] ??= { country: r.birth_country, flag: r.birth_flag, n: 0 };
			counts[r.birth_country].n += 1;
		});
	return Object.values(counts).sort((a, b) => b.n - a.n);
}

function renderDetail(f) {
	const p = f.properties;
	document.getElementById("detail-flags").textContent = flagString(p);
	document.getElementById("detail-address").textContent = p.address;
	document.getElementById("detail-meta").textContent =
		`${p.people} ${p.people === 1 ? "person" : "people"} · ${p.adults} over ${ADULT_OVER} · census sheet ${p.sheets.join(", ")}`;

	const top = new Set(flagsOf(p).map((c) => c.country));
	document.getElementById("detail-tally").innerHTML = tally(p)
		.map((c) => `<span class="tally-chip ${top.has(c.country) ? "top" : ""}">${c.flag} ${escapeHtml(c.country)} · ${c.n}</span>`)
		.join("");

	document.getElementById("detail-residents").innerHTML = p.residents
		.map((r) => {
			const flag = r.birth_flag;
			const parents =
				r.father_bp || r.mother_bp
					? ` · father ${escapeHtml(r.father_bp || "?")}, mother ${escapeHtml(r.mother_bp || "?")}`
					: "";
			const age = r.age ? `${escapeHtml(r.age)}` : "age not given";
			return `
				<li class="resident ${r.adult ? "" : "minor"}">
					<div class="flag">${flag}</div>
					<div>
						<div class="who">${escapeHtml(r.name)}${r.adult ? "" : '<span class="tag">under 17</span>'}${r.uncertain ? '<span class="tag unsure" title="Part of this row was hard to read">unsure</span>' : ""}</div>
						<div class="what">${escapeHtml(r.relation)} · ${r.sex === "F" ? "female" : r.sex === "M" ? "male" : escapeHtml(r.sex)}, ${age}
							· born ${escapeHtml(r.birthplace || "?")}${parents}
							${r.occupation ? `<br>${escapeHtml(r.occupation)}` : ""}</div>
					</div>
				</li>`;
		})
		.join("");

	const loc =
		p.geocode_confidence === "exact"
			? "Placed at today's address of the same number."
			: "Placed approximately: today's map has no exact match for this house number.";
	document.getElementById("detail-fineprint").textContent =
		`${loc} House numbers and street names may have changed since 1900. Only people over ${ADULT_OVER} count toward the flag.`;
}

function selectHouse(address) {
	const f = houses.find((h) => h.properties.address === address);
	if (!f) return;
	selected = address;
	refreshMarkers();
	markActiveRow();
	renderDetail(f);
	document.getElementById("house-detail").scrollTop = 0; // a new house starts at its top

	const panel = document.getElementById("panel");
	panel.classList.add("showing-detail");
	panel.classList.remove("peek");

	map.easeTo({
		center: f.geometry.coordinates,
		zoom: Math.max(map.getZoom(), 18),
		padding: mapPadding(),
		duration: 700,
	});
}

function showList() {
	selected = null;
	refreshMarkers();
	markActiveRow();
	document.getElementById("panel").classList.remove("showing-detail");
}

// --- Controls ---

const opacity = document.getElementById("opacity");
function setOpacity() {
	if (map.getLayer("sanborn")) map.setPaintProperty("sanborn", "raster-opacity", opacity.value / 100);
}
opacity.addEventListener("input", setOpacity);

document.getElementById("back-button").addEventListener("click", showList);

document.getElementById("panel-header").addEventListener("click", () => {
	if (!isMobile()) return;
	const panel = document.getElementById("panel");
	if (panel.classList.contains("showing-detail")) return;
	panel.classList.toggle("peek");
});

document.addEventListener("keydown", (e) => {
	if (e.key === "Escape" && selected) showList();
});

// --- Load ---

// Markers are DOM elements, so the census data doesn't wait for the map's "load" event
// (which waits for every basemap tile).
map.once("style.load", setOpacity);

(async () => {
	const res = await fetch(CENSUS_URL);
	houses = (await res.json()).features;

	buildMarkers();
	renderList();

	// Fit to the houses, unless the page was opened with a map view in the URL.
	if (!hadHashOnLoad && houses.length) {
		const b = new maplibregl.LngLatBounds();
		houses.forEach((f) => b.extend(f.geometry.coordinates));
		map.fitBounds(b, { padding: mapPadding(), maxZoom: 18, duration: 0 });
	}
})();
