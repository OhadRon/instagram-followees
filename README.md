# instagram-followees
An app to analyse some stats about the people you follow on instagram

##To Deploy Locally:

- Clone the repository
- Create an Instagram app at https://instagram.com/developer/clients/manage/
- Create an `.env` file with the required variables
- Install requirements by `pip install -r requirements.txt`
- Run the procfile with `heroku local`

##Environment variables required:

`CLIENT_ID=` You Instgaram client id

`CLIENT_SECRET=` client secret

`BASE_URL=` for example `http://localhost`

`DEBUG_MODE=` for example `FALSE` or `TRUE`

`PORT=` for example `80`
