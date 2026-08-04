export type AgentKey = 'director' | 'location' | 'scheduler' | 'budget' | 'risk'
export type AgentStatus = 'idle' | 'running' | 'complete'

export const AGENT_SEQUENCE: { key: AgentKey; label: string; short: string }[] = [
  { key: 'director', label: 'Director Agent', short: 'Director' },
  { key: 'location', label: 'Location Agent', short: 'Location' },
  { key: 'scheduler', label: 'Scheduler Agent', short: 'Scheduler' },
  { key: 'budget', label: 'Budget Agent', short: 'Budget' },
  { key: 'risk', label: 'Risk Agent', short: 'Risk' },
]

export type Scene = {
  id: number
  slug: string
  intExt: 'INT' | 'EXT'
  timeOfDay: 'DAY' | 'NIGHT' | 'DUSK' | 'DAWN'
  pages: number
  characters: string[]
  locationType: string
  props: string[]
  requirements: string[]
  synopsis: string
}

export const SCRIPT_TITLE = 'The Salt Flats'
export const SCRIPT_WRITER = 'M. Aldana'

export const SAMPLE_SCRIPT = `THE SALT FLATS
Written by M. Aldana

FADE IN:

EXT. MOJAVE SALT FLATS - DAWN

A cracked white plain stretches to the horizon. NORA (34) walks
the centerline of a road that no longer exists.

NORA (V.O.)
They told me the water left in a single night.
...`

export const SCENES: Scene[] = [
  {
    id: 1,
    slug: 'EXT. MOJAVE SALT FLATS — DAWN',
    intExt: 'EXT',
    timeOfDay: 'DAWN',
    pages: 1.5,
    characters: ['Nora', 'Field Crew (BG)'],
    locationType: 'Desert flat / open plain',
    props: ['Weathered duffel', 'Survey stakes', 'Field notebook'],
    requirements: ['Golden hour window', 'Drone permit', '4x4 crew transport', 'Dust mitigation'],
    synopsis: 'Nora crosses the dry lakebed at first light, narrating the night the water vanished.',
  },
  {
    id: 2,
    slug: 'INT. RESEARCH TRAILER — CONTINUOUS',
    intExt: 'INT',
    timeOfDay: 'DAY',
    pages: 2.25,
    characters: ['Nora', 'Dr. Vance', 'Ivo'],
    locationType: 'Practical trailer interior',
    props: ['Core samples', 'CRT monitors', 'Wall maps', 'Coffee percolator'],
    requirements: ['Generator power', 'Interior lighting rig', 'Sound blankets', 'Steadicam'],
    synopsis: 'The team argues over falsified aquifer readings while a storm builds outside.',
  },
  {
    id: 3,
    slug: 'EXT. ABANDONED PIER — DUSK',
    intExt: 'EXT',
    timeOfDay: 'DUSK',
    pages: 1.75,
    characters: ['Nora', 'Ivo'],
    locationType: 'Waterfront / derelict structure',
    props: ['Rusted lantern', 'Rope coil', 'Polaroid photos'],
    requirements: ['Tide schedule', 'Safety rigging', 'Marine unit standby', 'Practical fire FX'],
    synopsis: 'Ivo confesses what he buried under the pier the year the reservoir closed.',
  },
  {
    id: 4,
    slug: 'INT. COUNTY ARCHIVE — NIGHT',
    intExt: 'INT',
    timeOfDay: 'NIGHT',
    pages: 3.0,
    characters: ['Nora', 'Archivist', 'Deputy Reyes'],
    locationType: 'Institutional interior',
    props: ['Microfilm reader', 'Ledger boxes', 'Flashlight', 'Keyring'],
    requirements: ['Night shoot', 'Location after-hours access', 'Dolly track', 'Atmos haze'],
    synopsis: 'A break-in turns into discovery: forty years of redacted water rights.',
  },
  {
    id: 5,
    slug: 'EXT. HIGHWAY 190 OVERLOOK — DAY',
    intExt: 'EXT',
    timeOfDay: 'DAY',
    pages: 2.5,
    characters: ['Nora', 'Dr. Vance', 'Stunt Double'],
    locationType: 'Highway / elevated vista',
    props: ['Pickup truck (hero)', 'Blowout tire rig', 'Road flares'],
    requirements: ['Road closure permit', 'Stunt coordinator', 'Picture vehicles', 'CHP escort'],
    synopsis: 'A staged blowout forces Vance to reveal who is paying for the survey.',
  },
  {
    id: 6,
    slug: 'INT. MOTEL ROOM 12 — NIGHT',
    intExt: 'INT',
    timeOfDay: 'NIGHT',
    pages: 1.25,
    characters: ['Nora'],
    locationType: 'Motel practical',
    props: ['Cassette recorder', 'Pinboard of clippings', 'Ice bucket'],
    requirements: ['Night exterior spill', 'Neon sign practical', 'Minimal crew footprint'],
    synopsis: 'Nora replays the tape and hears a second voice she never recorded.',
  },
  {
    id: 7,
    slug: 'EXT. SALT FLATS — CLIMAX — NIGHT',
    intExt: 'EXT',
    timeOfDay: 'NIGHT',
    pages: 4.0,
    characters: ['Nora', 'Dr. Vance', 'Ivo', 'Deputy Reyes', 'Extras (24)'],
    locationType: 'Desert flat / open plain',
    props: ['Helicopter (picture)', 'Floodlight towers', 'Water tanker'],
    requirements: ['Aerial unit', 'Night lighting package', 'Crowd wrangling', 'Medic on set'],
    synopsis: 'Floodlights reveal the tanker convoy and the whole conspiracy at once.',
  },
]

export const TOTAL_PAGES = SCENES.reduce((sum, s) => sum + s.pages, 0)
export const RUNTIME_MINUTES = Math.round(TOTAL_PAGES)

export type LocationOption = {
  id: string
  name: string
  region: string
  scenes: number[]
  costPerDay: number
  distanceKm: number
  travelMinutes: number
  weather: 'clear' | 'cloudy' | 'rain' | 'wind'
  tempC: number
  environment: 'indoor' | 'outdoor'
  weatherDependent: boolean
  permitRequired: boolean
  matchScore: number
  lat: number
  lng: number
  image: string
  notes: string
}

export const LOCATIONS: LocationOption[] = [
  {
    id: 'loc-salt',
    name: 'Badwater Salt Basin',
    region: 'Death Valley, CA',
    scenes: [1, 7],
    costPerDay: 4200,
    distanceKm: 38,
    travelMinutes: 42,
    weather: 'clear',
    tempC: 34,
    environment: 'outdoor',
    weatherDependent: true,
    permitRequired: true,
    matchScore: 96,
    lat: 36.2296,
    lng: -116.7666,
    image: '/locations/salt-flats.png',
    notes: 'Unbroken 4km sightlines, no power on site — generator package required.',
  },
  {
    id: 'loc-trailer',
    name: 'Furnace Creek Field Station',
    region: 'Death Valley, CA',
    scenes: [2],
    costPerDay: 1850,
    distanceKm: 12,
    travelMinutes: 16,
    weather: 'clear',
    tempC: 31,
    environment: 'indoor',
    weatherDependent: false,
    permitRequired: false,
    matchScore: 91,
    lat: 36.4642,
    lng: -116.8694,
    image: '/locations/research-trailer.png',
    notes: 'Practical trailer with hard power and shaded crew parking.',
  },
  {
    id: 'loc-pier',
    name: 'Salton Sea North Pier',
    region: 'Imperial County, CA',
    scenes: [3],
    costPerDay: 3100,
    distanceKm: 264,
    travelMinutes: 212,
    weather: 'wind',
    tempC: 27,
    environment: 'outdoor',
    weatherDependent: true,
    permitRequired: true,
    matchScore: 88,
    lat: 33.5216,
    lng: -115.9128,
    image: '/locations/abandoned-pier.png',
    notes: 'Structural survey required before crew load-in. Tide-independent.',
  },
  {
    id: 'loc-archive',
    name: 'Inyo County Records Hall',
    region: 'Independence, CA',
    scenes: [4],
    costPerDay: 2400,
    distanceKm: 96,
    travelMinutes: 84,
    weather: 'cloudy',
    tempC: 18,
    environment: 'indoor',
    weatherDependent: false,
    permitRequired: true,
    matchScore: 84,
    lat: 36.8027,
    lng: -118.1998,
    image: '/locations/county-archive.png',
    notes: 'After-hours access only, 22:00–05:00. Marble acoustics need treatment.',
  },
  {
    id: 'loc-highway',
    name: 'Highway 190 Overlook',
    region: 'Panamint Range, CA',
    scenes: [5],
    costPerDay: 5600,
    distanceKm: 54,
    travelMinutes: 61,
    weather: 'clear',
    tempC: 24,
    environment: 'outdoor',
    weatherDependent: true,
    permitRequired: true,
    matchScore: 79,
    lat: 36.3419,
    lng: -117.0855,
    image: '/locations/highway-overlook.png',
    notes: 'Rolling closure approved for 6h blocks. CHP escort billed hourly.',
  },
  {
    id: 'loc-motel',
    name: 'Amargosa Motor Lodge',
    region: 'Amargosa Valley, NV',
    scenes: [6],
    costPerDay: 1200,
    distanceKm: 71,
    travelMinutes: 68,
    weather: 'clear',
    tempC: 22,
    environment: 'indoor',
    weatherDependent: false,
    permitRequired: false,
    matchScore: 93,
    lat: 36.5783,
    lng: -116.4194,
    image: '/locations/motel-room.png',
    notes: 'Period-correct neon still functional. Doubles as unit base.',
  },
]

export type ShootBlock = {
  id: string
  day: number
  date: string
  locationId: string
  scenes: number[]
  callTime: string
  wrapTime: string
  unit: 'Main Unit' | 'Second Unit' | 'Aerial Unit'
  conflict?: string
}

export const SCHEDULE: ShootBlock[] = [
  {
    id: 'blk-1',
    day: 1,
    date: 'Mon, Sep 8',
    locationId: 'loc-trailer',
    scenes: [2],
    callTime: '07:00',
    wrapTime: '18:30',
    unit: 'Main Unit',
  },
  {
    id: 'blk-2',
    day: 2,
    date: 'Tue, Sep 9',
    locationId: 'loc-salt',
    scenes: [1],
    callTime: '04:30',
    wrapTime: '13:00',
    unit: 'Main Unit',
    conflict: 'Dawn window is 41 min — no coverage margin if camera is late.',
  },
  {
    id: 'blk-3',
    day: 3,
    date: 'Wed, Sep 10',
    locationId: 'loc-highway',
    scenes: [5],
    callTime: '06:00',
    wrapTime: '19:00',
    unit: 'Main Unit',
    conflict: 'Road closure permit pending — CHP confirmation outstanding.',
  },
  {
    id: 'blk-4',
    day: 4,
    date: 'Thu, Sep 11',
    locationId: 'loc-motel',
    scenes: [6],
    callTime: '16:00',
    wrapTime: '02:00',
    unit: 'Main Unit',
  },
  {
    id: 'blk-5',
    day: 5,
    date: 'Fri, Sep 12',
    locationId: 'loc-archive',
    scenes: [4],
    callTime: '21:00',
    wrapTime: '05:30',
    unit: 'Main Unit',
    conflict: 'Deputy Reyes actor unavailable before 23:00 (theatre commitment).',
  },
  {
    id: 'blk-6',
    day: 6,
    date: 'Mon, Sep 15',
    locationId: 'loc-pier',
    scenes: [3],
    callTime: '13:00',
    wrapTime: '22:00',
    unit: 'Main Unit',
    conflict: 'Sustained 35 km/h wind forecast — marine safety hold likely.',
  },
  {
    id: 'blk-7',
    day: 7,
    date: 'Tue, Sep 16',
    locationId: 'loc-salt',
    scenes: [7],
    callTime: '15:00',
    wrapTime: '04:00',
    unit: 'Aerial Unit',
  },
]

export const SHOOT_DAYS = SCHEDULE.length

export type Constraint = {
  id: string
  kind: 'actor' | 'crew' | 'weather'
  name: string
  detail: string
  severity: 'low' | 'medium' | 'high'
}

export const CONSTRAINTS: Constraint[] = [
  {
    id: 'c1',
    kind: 'actor',
    name: 'Nora (lead)',
    detail: 'Available all 7 days. Contract caps nights at 3 — currently scheduled 4.',
    severity: 'medium',
  },
  {
    id: 'c2',
    kind: 'actor',
    name: 'Deputy Reyes',
    detail: 'Unavailable before 23:00 on Sep 12. Blocks Day 5 first unit.',
    severity: 'high',
  },
  {
    id: 'c3',
    kind: 'actor',
    name: 'Dr. Vance',
    detail: 'Hard out Sep 16 at 22:00 — climax needs coverage before wrap.',
    severity: 'high',
  },
  {
    id: 'c4',
    kind: 'crew',
    name: 'Aerial unit',
    detail: 'Single-day booking only, held for Sep 16. No weather backup date.',
    severity: 'medium',
  },
  {
    id: 'c5',
    kind: 'crew',
    name: 'Stunt coordinator',
    detail: 'Confirmed Sep 10 only. Blowout rig requires a 4h pre-light.',
    severity: 'low',
  },
  {
    id: 'c6',
    kind: 'weather',
    name: 'Salton Sea wind',
    detail: '78% chance of 30+ km/h gusts on Sep 15. Move or add cover set.',
    severity: 'high',
  },
  {
    id: 'c7',
    kind: 'weather',
    name: 'Death Valley heat',
    detail: 'Forecast 41 °C on Sep 9 — mandated cooling breaks every 90 min.',
    severity: 'medium',
  },
]

export type BudgetCategory = {
  key: string
  label: string
  amount: number
  min: number
  max: number
  note: string
}

export const BUDGET_CATEGORIES: BudgetCategory[] = [
  {
    key: 'locations',
    label: 'Locations',
    amount: 182_000,
    min: 90_000,
    max: 320_000,
    note: 'Permits, site fees, restoration bonds',
  },
  {
    key: 'equipment',
    label: 'Equipment',
    amount: 146_000,
    min: 80_000,
    max: 280_000,
    note: 'Camera, lighting, grip, aerial package',
  },
  {
    key: 'crew',
    label: 'Crew',
    amount: 264_000,
    min: 160_000,
    max: 420_000,
    note: '48 crew across 7 shoot days incl. overtime',
  },
  {
    key: 'transportation',
    label: 'Transportation',
    amount: 78_000,
    min: 40_000,
    max: 160_000,
    note: 'Picture vehicles, unit moves, fuel',
  },
  {
    key: 'contingency',
    label: 'Contingency',
    amount: 52_000,
    min: 20_000,
    max: 120_000,
    note: '10% reserve against weather holds',
  },
]

export type Risk = {
  id: string
  title: string
  category: 'Weather' | 'Permits' | 'Budget' | 'Scheduling' | 'Safety'
  severity: 'low' | 'medium' | 'high'
  scope: string
  likelihood: number
  impact: string
  recommendation: string
}

export const RISKS: Risk[] = [
  {
    id: 'r1',
    title: 'Wind hold at Salton Sea pier',
    category: 'Weather',
    severity: 'high',
    scope: 'Scene 3 · Day 6',
    likelihood: 78,
    impact: 'Full day loss (~$46k) if marine unit stands down.',
    recommendation:
      'Bank INT. Motel cover set on Day 6 and shift the pier to Sep 17 when gusts drop to 14 km/h.',
  },
  {
    id: 'r2',
    title: 'Highway 190 closure permit unconfirmed',
    category: 'Permits',
    severity: 'high',
    scope: 'Scene 5 · Day 3',
    likelihood: 64,
    impact: 'Stunt day cannot proceed without CHP escort; coordinator is single-day.',
    recommendation:
      'Escalate to Inyo County film office today and pre-book a second stunt date as insurance.',
  },
  {
    id: 'r3',
    title: 'Lead actor night-work cap exceeded',
    category: 'Scheduling',
    severity: 'medium',
    scope: 'Nora · Days 4, 5, 7',
    likelihood: 55,
    impact: 'Contractual penalty plus turnaround violation on Day 7 call.',
    recommendation: 'Move Scene 6 to a day-for-night interior and reclaim one night from the cap.',
  },
  {
    id: 'r4',
    title: 'Aerial unit has no weather backup',
    category: 'Scheduling',
    severity: 'medium',
    scope: 'Scene 7 · Day 7',
    likelihood: 48,
    impact: 'Climax coverage incomplete; reshoot estimated at $88k.',
    recommendation: 'Hold a contingent Sep 17 aerial slot and shoot ground plates on Day 2.',
  },
  {
    id: 'r5',
    title: 'Equipment line trending 12% over',
    category: 'Budget',
    severity: 'medium',
    scope: 'Whole production',
    likelihood: 61,
    impact: 'Projected $146k vs $130k approved for camera and lighting.',
    recommendation: 'Consolidate the night lighting package across Days 4, 5 and 7 to one rental block.',
  },
  {
    id: 'r6',
    title: 'Heat exposure on salt basin',
    category: 'Safety',
    severity: 'medium',
    scope: 'Scenes 1, 7 · Days 2, 7',
    likelihood: 42,
    impact: 'Mandated cooling breaks reduce effective shoot hours by ~18%.',
    recommendation: 'Add shade structures and a second medic; schedule setups before 10:00.',
  },
  {
    id: 'r7',
    title: 'Archive marble acoustics',
    category: 'Safety',
    severity: 'low',
    scope: 'Scene 4 · Day 5',
    likelihood: 30,
    impact: 'Dialogue reverb may force ADR on 3 pages.',
    recommendation: 'Pre-rig sound blankets during the 4h pre-light window.',
  },
  {
    id: 'r8',
    title: 'Restoration bond on protected flats',
    category: 'Permits',
    severity: 'low',
    scope: 'Scenes 1, 7',
    likelihood: 25,
    impact: '$18k bond held 60 days post-wrap; affects cashflow, not schedule.',
    recommendation: 'File the surface-impact plan early to qualify for the reduced bond tier.',
  },
]

export const RISK_SCORE = 62

export function formatCurrency(value: number, compact = false) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 1 : 0,
  }).format(value)
}
