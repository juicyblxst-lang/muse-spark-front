# Muse Memory Canvas

Build the Muse frontend as a standalone Next.js + TypeScript application.

Muse is an AI-powered creative memory application. Users upload old creative material such as PDFs, DOCX files, TXT files and Markdown files. Muse processes those documents, remembers the ideas, entities, relationships and timelines, and later helps users rediscover and revive abandoned ideas.

Build ONLY the frontend at this stage.

Do not implement:

- document parsing

- AI extraction

- entity resolution

- relationship extraction

- temporal analysis

- Sibyl integration

- OpenClaw

- backend processing

- database logic

Create the frontend architecture so those capabilities can later connect through a clean HTTP API.

Required screens:

1. Landing page

2. Authentication

3. Dashboard

4. Upload interface

5. Processing state

6. Document library

7. Document detail

8. Memory/search interface

9. Memory detail

10. Timeline

11. Relationships/connections

12. Revival results

13. Source/provenance view

14. Correction interface

15. Settings

The UI must be designed around the actual Muse workflow:

User uploads material

→ Muse processes it

→ user sees what was discovered

→ user searches their memory

→ Muse surfaces forgotten material

→ user asks Muse to revive an idea.

Use mock data only.

Create explicit TypeScript interfaces for every API response the future backend will provide.

Do not invent backend endpoints outside the API contract documented in the project.

Keep the frontend modular so the mock data layer can later be replaced with real API calls without rewriting the UI.

At completion:

- application builds successfully

- all routes render

- no backend dependency exists

- no fake AI logic exists

- TypeScript passes

- components are reusable

- API types are centralized

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/a3bf9682-dc4c-4961-90c3-94cb22165b8c).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
