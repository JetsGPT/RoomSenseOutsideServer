function Terms() {
  return (
    <div className="container py-8 animate-fade-in">
      <h1 className="mb-4">General Terms and Conditions (GTC) for RoomSense</h1>
      <p className="text-muted mb-4">
        Date: January 2026 | Provider: Project Team "JetsGPT" (Diploma Project of HTL Donaustadt)
      </p>

      <div className="card mb-4">
        <h3 className="mb-4">§ 1 Scope and Project Status</h3>
        <p className="mb-4">
          These General Terms and Conditions (hereinafter referred to as "GTC") govern the use of the hardware 
          and software solution "RoomSense" (hereinafter referred to as "Service"), provided by the project team 
          JetsGPT (hereinafter referred to as "Provider").
        </p>
        <div className="alert-warning mb-4">
          <strong>Important Note regarding Project Status:</strong> The user acknowledges that RoomSense is a 
          diploma project within the framework of an academic education. The software and hardware are provided 
          "as is". There is no claim to continuous availability, commercial warranty, or professional support.
        </div>
      </div>

      <div className="card mb-4">
        <h3 className="mb-4">§ 2 Subject of Service</h3>
        <p className="mb-4">The Service includes the following components, as described in the project documentation:</p>
        <ul style={{ listStyle: 'disc', paddingLeft: '1.5rem' }} className="mb-4">
          <li className="mb-2">
            <strong>The Hardware ("The Box"):</strong> An IoT sensor node for measuring environmental data 
            (temperature, humidity, air quality, etc.).
          </li>
          <li className="mb-2">
            <strong>The Software Platform:</strong> Access to the web dashboard for data visualization via the React App.
          </li>
          <li className="mb-2">
            <strong>API Access:</strong> Interfaces for retrieving sensor data and for integration into third-party systems.
          </li>
          <li className="mb-2">
            <strong>Backend Services:</strong> Storage of data in databases (PostgreSQL, InfluxDB) and routing 
            via the Forwarding Server.
          </li>
        </ul>
      </div>

      <div className="card mb-4">
        <h3 className="mb-4">§ 3 Registration and Security</h3>
        <p className="mb-4">
          Registration is required to use the dashboard. The user agrees to provide truthful information.
        </p>
        <p className="mb-4">
          <strong>Credentials:</strong> The user is responsible for keeping their password confidential. 
          On the server side, passwords are stored encrypted using Bcrypt and salt. However, the protection 
          of the end device is the responsibility of the user.
        </p>
        <p className="mb-4">
          <strong>Reporting Obligation:</strong> In case of suspected misuse of the account, the Provider 
          must be informed immediately.
        </p>
      </div>

      <div className="card mb-4">
        <h3 className="mb-4">§ 4 Use of the API and Fair Use (Rate Limiting)</h3>
        <p className="mb-4">
          Access to the API is subject to technical restrictions to ensure system stability for all users.
        </p>
        <p className="mb-4"><strong>Rate Limits:</strong> The user accepts the implemented access restrictions:</p>
        <ul style={{ listStyle: 'disc', paddingLeft: '1.5rem' }} className="mb-4">
          <li className="mb-2"><strong>Authenticated Requests:</strong> Maximum 120 requests per 60 seconds.</li>
          <li className="mb-2"><strong>Login Attempts:</strong> Maximum 20 requests per 60 seconds.</li>
        </ul>
        <p className="mb-4">Exceeding these limits will result in a temporary block (HTTP Status 429).</p>
        <div className="alert-danger mb-4">
          Any attempt to bypass these security mechanisms (e.g., DDoS attacks, "hammering") will result in 
          the immediate suspension of the account.
        </div>
      </div>

      <div className="card mb-4">
        <h3 className="mb-4">§ 5 Exclusion of Liability for Automations</h3>
        <p className="mb-4">
          RoomSense offers functions to trigger actions based on sensor data 
          (e.g., "Switch on air conditioning if temperature &gt; 30°C").
        </p>
        <div className="alert-warning mb-4">
          <strong>Warning:</strong> The user acknowledges that malfunctions (e.g., sensor failure, 
          connection loss, software bugs) cannot be ruled out.
        </div>
        <p className="mb-4">
          <strong>Exclusion of Liability:</strong> The Provider is not liable for damages resulting from 
          automated switching operations. This includes in particular, but not limited to:
        </p>
        <ul style={{ listStyle: 'disc', paddingLeft: '1.5rem' }} className="mb-4">
          <li className="mb-2">Energy costs due to permanently running devices.</li>
          <li className="mb-2">Damages caused by devices not being switched on (e.g., overheating).</li>
          <li className="mb-2">Physical damages caused by incorrect control signals.</li>
        </ul>
        <div className="alert-danger">
          <strong>The use of RoomSense in safety-critical areas (e.g., medical monitoring, fire protection) 
          is prohibited.</strong>
        </div>
      </div>

      <div className="card mb-4">
        <h3 className="mb-4">§ 6 Data Protection</h3>
        <p className="mb-4">
          <strong>Sensor Data:</strong> The environmental data collected by the user is stored in an InfluxDB database.
        </p>
        <p className="mb-4">
          <strong>Personal Data:</strong> Username, password hash, and roles are stored in a PostgreSQL database 
          for login and administration purposes.
        </p>
        <p className="mb-4">
          Data will not be passed on to third parties unless this is necessary for the technical provision 
          of the Service or required by law.
        </p>
      </div>

      <div className="card mb-4">
        <h3 className="mb-4">§ 7 Hardware and Assembly</h3>
        <p className="mb-4">
          The "RoomSense" box is a prototype. Assembly and wiring are carried out at the user's own risk.
        </p>
        <p className="mb-4">
          The Provider assumes no liability for damage to walls, furniture, or electrical house installations 
          caused by assembly (e.g., magnetic pin fittings).
        </p>
        <p className="mb-4">
          The user must ensure that the hardware (especially power supply units) complies with local safety regulations.
        </p>
      </div>

      <div className="card mb-4">
        <h3 className="mb-4">§ 8 Changes and Termination</h3>
        <p className="mb-4">
          As this is an ongoing development project, the Provider reserves the right to change, extend, 
          or discontinue functions at any time ("Feature Updates").
        </p>
        <p className="mb-4">
          The user may request the deletion of their account at any time.
        </p>
        <p className="mb-4">
          The Provider is entitled to discontinue the Service – particularly after the completion of the diploma project.
        </p>
      </div>

      <div className="card">
        <h3 className="mb-4">§ 9 Jurisdiction and Applicable Law</h3>
        <p className="mb-4">Austrian law applies.</p>
        <p className="mb-4">Place of performance and jurisdiction is Vienna (Location of HTL Donaustadt).</p>
        <p className="text-muted" style={{ fontSize: '0.875rem', marginTop: '2rem' }}>
          Updated: January 2026
        </p>
      </div>
    </div>
  )
}

export default Terms
