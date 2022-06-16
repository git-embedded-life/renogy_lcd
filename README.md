After purchasing a Renogy Inverter/Charger for the purpose of powering our sump pump in the event of a black-out, I decided I wanted to expand its purpose to also power my ~125W of network equipment. This included a NetGate pfSense appliance, and a Dell Server. The trick was, unlike traditional UPS's that have a means of communicating with the connected device to notify when the battery was low, the Renogy did not have this. The Renogy does have a RJ45 port that has no documentation, and a LCD display. My first thought was to reverse the RJ45 port, but my fear was that I was going to damage the device not knowing anything about the port. I ended up taking what I though was the safer route; use a Pi with an attached camera to read the information I needed from the display. The information is then passed on to a dummy UPS in [NUT](https://networkupstools.org/).

## Setup
<image src="images/setup_50.jpg" width="50%">

## Image captured by the Pi
<image src="images/initial.jpg" width="50%">

## Processed image
<image src="images/processed.jpg" width="50%">