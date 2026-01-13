const teamMembers = [
  {
    name: 'Tobias Nesvadba',
    role: 'Team Lead & Coordinator',
    description: 'Oversees the project structure and keeps delivery on track.',
    emoji: '👨‍💻'
  },
  {
    name: 'Eray Yesildag',
    role: 'Implementation Lead',
    description: 'Turns product ideas into reliable hardware and firmware.',
    emoji: '🛠️'
  },
  {
    name: 'Julian Prakisch',
    role: 'Sustainability Advocate',
    description: 'Shapes the vision and keeps the product eco-conscious.',
    emoji: '🌱'
  },
  {
    name: 'Sebastian Romano',
    role: 'Product Design',
    description: 'Brings creativity and a user-first perspective to the experience.',
    emoji: '🎨'
  }
]

function Team() {
  return (
    <div className="container py-8 animate-fade-in">
      <h1 className="mb-4 text-center">Meet the RoomSense Outside Crew</h1>
      <div className="flex gap-8 justify-center" style={{ flexWrap: 'wrap', marginTop: '1.5rem' }}>
        {teamMembers.map((member) => (
          <div 
            key={member.name}
            className="card text-center" 
            style={{ flex: 1, minWidth: '250px', maxWidth: '300px' }}
          >
            <div style={{ 
              width: '100px', 
              height: '100px', 
              backgroundColor: 'var(--muted)', 
              borderRadius: '50%', 
              margin: '0 auto 1rem auto', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              fontSize: '2rem' 
            }}>
              {member.emoji}
            </div>
            <h3>{member.name}</h3>
            <p className="text-primary" style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>
              {member.role}
            </p>
            <p style={{ fontSize: '0.875rem' }}>{member.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Team
