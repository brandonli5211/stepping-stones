# Genesys conversation PoC

A single conversation flowing through Python, MongoDB, Spring Boot, and React. The MongoDB document uses a string `_id` of `"1"` and stores transcript entries as `{ "speaker", "text" }` objects.

## Run it

1. Start MongoDB on port 27017.
2. From this directory, install the dependency and load the three-conversation ABCD preview from the official repository:

   ```sh
   pip install -r requirements.txt
   python3 load_conversation.py
   ```

   The loader replaces the demo records in genesys_poc.conversations. API IDs 1, `2`, and 3 map to the sample's original ABCD conversation IDs. It needs an internet connection to fetch the preview from [the ABCD repository](https://github.com/asappresearch/abcd).

3. Start the Java API:

   ```sh
   cd backend-java
   mvn spring-boot:run
   ```

   It reads genesys_poc.conversations and serves `GET http://localhost:8080/api/conversation/1`.

4. Create the React app once, then copy this directory's `App.js` over `frontend-react-app/src/App.js`:

   ```sh
   npx create-react-app frontend-react-app
   ```

   On Windows PowerShell, run `Copy-Item App.js frontend-react-app/src/App.js` from the project root.

   In another terminal, start the frontend:

   ```sh
   cd frontend-react-app
   npm start
   ```
