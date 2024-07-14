# TenBet

TenBet is a sports prediction app writen on Python.
The application uses standard tools:

- MongoDB for data storage
- Pydantic for working with data
- Sklearn for building predictive models

The following data sources are currently used:

- flashscore.com for collecting sports statistics
- betexplorer.com for collecting bookmakers quotes
- tennisexplorer.com for collecting additional tennis statistics

The main goal of the project is to provide opportunities for analytics (including predictive) for a wide variety of sports.
Each sport is a separate and complex project that could potentially have its own specifics.
TenBet tries to take this into account through architectural requirements.

# Features of the first version.

The first version of the project provides opportunities for further development of any sport.
Here are the basic tools for work. Basic implementations will help you get basic results right away: from data to predictions.
TenBet does not have a "developed" client interface. Instead, the project provides functionality that can be easily integrated into any interface.

The project is not fully covered by tests, is in a fairly raw state and may produce unexpected errors.
