/**
 * Description: Read and decrypt data from the Citizen Card.
 * This script doesn't take in consideration several use cases and error handling. The purpose is just for debugging and testing.
 * Author: Tragio.pt
 */

const backendUrl = 'http://127.0.0.1:8000'
const DISCOVERY_CONFIG = {
  PORTS: [35153, 43456, 47920, 57379, 64704],
  TIMEOUT: 5000,
  LOCAL_URL: 'http://127.0.0.1',
  CLOUD_URL: 'https://m{n}.mordomo.gov.pt',
  MAX_INSTANCES: 20,
}

const responsesList = []
const readRequestData = {}
const readEncryptedData = {}
const discoveredEndpoint = {}

// Update responses list
function updateResponses() {
  const responsesDiv = document.getElementById('responses')
  responsesDiv.style.display = 'block'
  responsesDiv.innerHTML = responsesList
    .map((response) => `<article>${JSON.stringify(response)}</article>`)
    .join('')
}

// Generate random instances for cloud endpoints
const getRandomInstances = (count) => {
  const instances = new Set()
  while (instances.size < count) {
    instances.add(
      Math.floor(Math.random() * DISCOVERY_CONFIG.MAX_INSTANCES) + 1
    )
  }
  return [...instances]
}

// Discover the "plugin Autenticação.Gov" instance
async function discoverService() {
  const endpoints = []

  // Add 5 local endpoints (one per port)
  DISCOVERY_CONFIG.PORTS.slice(0, 5).forEach((port) => {
    endpoints.push({
      url: `${DISCOVERY_CONFIG.LOCAL_URL}:${port}`,
    })
  })

  // Add 5 cloud endpoints with random instances
  const cloudInstances = getRandomInstances(5)
  cloudInstances.forEach((instance, index) => {
    endpoints.push({
      url: `${DISCOVERY_CONFIG.CLOUD_URL.replace('{n}', instance)}:${
        DISCOVERY_CONFIG.PORTS[index]
      }`,
    })
  })

  // Attempt to connect to all endpoints
  const attempts = endpoints.map(({ url }) => {
    return (
      Promise.race([
        // Fetch isAlive endpoint
        pluginIsAlive(true, url),

        // Timeout for each attempt
        new Promise((_, reject) =>
          setTimeout(
            () => reject(new Error(`Timeout for ${url}`)),
            DISCOVERY_CONFIG.TIMEOUT
          )
        ),
      ])
        // Catch errors and return null
        .catch((error) => {
          console.debug(`Failed to connect to ${url}: ${error.message}`)
          return null
        })
    )
  })

  // Race all attempts, return on first success
  const success = await Promise.race([
    ...attempts.map(async (attempt) => {
      const result = await attempt
      if (result) return result
      return new Promise(() => {}) // Never resolves if not successful
    }),

    // Fallback promise that rejects if no endpoint responds
    new Promise((_, reject) =>
      setTimeout(
        () => reject(new Error('Service not found after trying all endpoints')),
        DISCOVERY_CONFIG.TIMEOUT
      )
    ),
  ])

  // Update discovered endpoint
  Object.assign(discoveredEndpoint, {
    proto: success.proto,
    baseUrl: success.url,
    port: new URL(success.url).port,
    uuid: success.data.uuid,
  })

  console.log(`Successfully connected to ${success.url}`)
  return true
}

// Handle requests
async function handleRequest(url, options = {}, processData) {
  try {
    const response = await fetch(url, options)
    const data = await response.json()
    processData(data)
    responsesList.push(data)
  } catch (error) {
    responsesList.push({ error: error.message })
  } finally {
    updateResponses()
  }
}

// Check if the plugin is alive
async function pluginIsAlive(skipDiscovery = false, url) {
  if (!skipDiscovery && !discoveredEndpoint.baseUrl) {
    await discoverService()
  }

  const response = await fetch(`${url || discoveredEndpoint.baseUrl}/isAlive`, {
    method: 'POST',
  })
  const data = await response.json()
  // Update discovered endpoint UUID if already exists
  if (discoveredEndpoint.uuid) {
    discoveredEndpoint.uuid = data.uuid
  }
  return { url, data } // Return both URL and data
}

// Ask backend for the initial certificates
async function readRequest() {
  await handleRequest(
    `${backendUrl}/read/request`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent: discoveredEndpoint.uuid,
        cms: crypto.randomUUID(),
      }),
    },
    (data) => Object.assign(readRequestData, data)
  )
}

// Ask the plugin for the encrypted card data
async function pluginReadRequest() {
  if (!discoveredEndpoint.baseUrl) await discoverService()

  readRequestData.nc = true // Use the new cipher
  readRequestData.ccv2 = true // Enable support for CC V2

  const formData = new FormData()
  Object.entries(readRequestData).forEach(([key, value]) =>
    formData.append(key, value)
  )

  await handleRequest(
    `${discoveredEndpoint.baseUrl}/cc-read`,
    { method: 'POST', body: formData },
    (data) => Object.assign(readEncryptedData, data)
  )
}

// Ask the backend to decrypt the card data
async function readDelivery() {
  await handleRequest(
    `${backendUrl}/read/delivery`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(readEncryptedData),
    },
    (data) => {
      const dataDisplay = document.getElementById('ccDataDisplay')
      dataDisplay.textContent = JSON.stringify(data.data.card, null, 2)
      document.getElementById('photoDisplay').src = data.data.photo
      document.getElementById('finalData').style.display = 'block'
    }
  )
}

// Run the chain of functions
async function runChain() {
  if (!discoveredEndpoint.baseUrl) {
    await discoverService()
  } else {
    await pluginIsAlive()
  }

  await readRequest()
  await pluginReadRequest()
  await readDelivery()
}
