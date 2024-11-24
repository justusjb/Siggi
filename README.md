# Siggi

*Bridging Generations, Revolutionizing Housing*

Inspired by a [French government initiative](https://www.service-public.fr/particuliers/actualites/A17556?lang=en) encouraging elderly people to rent a room to a young tenant and live together, Siggi matches a host with a renter. To make this process painless, Siggi writes the contract based on the pair's requirements which they can just sign.

Importantly, Siggi doesn't just make existing housing even more competitive - it creates new opportunities, fostering intergenerational symbioses in the process.

## What it does
For this year's hackaTUM, we decided to revolutionize the housing market: Siggi is an AI agent that interacts with each generation through their preferred means of communication and quickly drafts a contract to sign.
This means that Siggi
1. talks to hosts by phone and to the younger generation via WhatsApp,
2. matches a renter to a host,
3. creates a contract, sending a [Docusign](https://www.docusign.com/) link to the renter and a paper copy to the host.

## How we built it
Siggi is comprised of 3 main parts: We used [Twilio](https://www.twilio.com/en-us) to provide a phone number and interface with the WhatsApp Business API. We used [Retell AI](https://www.retellai.com/) for low-latency voice agents, providing a smooth phone call experience. And we used Python with FastAPI to piece them together and implement the matching algorithm.

## Accomplishments that we're proud of
While creating each component was a challenge, integrating them proved the hardest. Twilio doesn't work well with AI agents directly so we had to come up with a way to use Retell AI. Additionally, we had to start drafting the contract during the ongoing phone call to eliminate disruptive wait times.

Ultimately, the integration was a great success: Siggi provides a streamlined flow to offer and rent housing.

## What we learned
We learned how to use Twilio, that Twilio+Gemini is too slow, and that Retell AI is way faster. The only uncertainty we're still left with is what "elastic SIP trunking" means...

## What's next for Siggi
By offering an easy way for people to let empty rooms, Siggi creates housing and intergenerational friendships.
The only task left is to integrate a online mailing service such as [LetterStream](https://www.letterstream.com/) to send the contract to the host and seal the deal, which we are excited to do in the coming week!

## Run project
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
