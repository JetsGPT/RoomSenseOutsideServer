function About() {
  return (
    <div className="container py-8 animate-fade-in">
      <div className="card mt-4">
        <h2>Our Mission</h2>
        <p className="mt-4">
          Residential buildings, schools, and homes frequently suffer from the absence of a system that delivers
          precise, real-time environmental and occupancy data.
          RoomSense equips users with actionable insights, enabling them to formulate their own automation or
          management strategies.
        </p>
        <p className="mt-4">
          By delivering precise and scalable data collection, we lay the groundwork for more informed
          decision-making in buildings.
        </p>
      </div>

      <div className="card mt-4">
        <h2>Market Analysis</h2>
        <p className="mt-4">
          <strong>Total Addressable Market (TAM):</strong> There are around 601,300 small businesses and 4.12
          million private households in Austria alone.
          The smart home market is expected to expand by ~82% yearly, reaching 2.6 million households by 2028.
        </p>
        <p className="mt-4">
          <strong>The Need:</strong> Many companies struggle with digitization and rising energy costs. RoomSense
          provides a solution to optimize energy usage and improve environmental conditions.
        </p>
      </div>

      <div className="flex gap-8 mt-4" style={{ flexWrap: 'wrap' }}>
        <div className="card" style={{ flex: 1 }}>
          <h3>USP (Unique Selling Point)</h3>
          <p className="mt-4">
            A modular, user-friendly sensor box that combines multiple environmental sensors (Air Quality, Temp,
            Humidity, Noise, Occupancy) with an open API and customizable automation events.
          </p>
        </div>
        <div className="card" style={{ flex: 1 }}>
          <h3>Target Audience</h3>
          <p className="mt-4">
            From tech-savvy developers who want to code their own automations, to business owners needing energy
            insights, to homeowners wanting a healthier living space.
          </p>
        </div>
      </div>
    </div>
  )
}

export default About
