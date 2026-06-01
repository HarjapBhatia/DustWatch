import { useMemo, useState } from 'react'

import { StatsBar } from './components/StatsBar'
import { Sidebar } from './components/Sidebar'
import { MapView } from './components/Map'
import { SiteCard } from './components/SiteCard'
import { useSites } from './hooks/useSites'
import type { CityStats, ConstructionSite } from './types'

const emptyStats: CityStats = {
	totalSites: 0,
	critical: 0,
	high: 0,
	medium: 0,
	low: 0,
	unregistered: 0,
	populationExposed: 0,
	lastUpdated: new Date().toISOString()
}

function App() {
	const { sites, stats, loading, error } = useSites()
	const [selectedSite, setSelectedSite] = useState<ConstructionSite | null>(null)

	const selectedId = selectedSite?.id ?? null
	const statsValue = useMemo(() => stats ?? emptyStats, [stats])

	return (
		<div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
			<StatsBar stats={statsValue} />
			{loading && (
				<div style={{ padding: '8px 16px', fontSize: 14, color: '#444' }}>
					Loading site data...
				</div>
			)}
			{error && (
				<div style={{ padding: '8px 16px', fontSize: 14, color: '#9B1C1C' }}>
					{error}
				</div>
			)}
			<div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
				<div style={{ width: 280, borderRight: '1px solid #ddd', minHeight: 0 }}>
					<Sidebar
						sites={sites}
						selectedId={selectedId}
						onSelect={setSelectedSite}
					/>
				</div>
				<div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
					<div style={{ flex: 1, minHeight: 0 }}>
						<MapView
							sites={sites}
							selectedId={selectedId}
							onSiteClick={setSelectedSite}
						/>
					</div>
					{selectedSite && (
						<div style={{ borderTop: '1px solid #ddd' }}>
							<SiteCard site={selectedSite} onClose={() => setSelectedSite(null)} />
						</div>
					)}
				</div>
			</div>
		</div>
	)
}

export default App
