# Rolling residency calculator

Made this calculator to keep track of the number of days I spend outside the UK in any coninuous period of 365 days.

Useful for frequent travellers who intend to apply for the ILR (Indefinite Leave to Remain) and want to prevent accidentally violating the residency requirements.

## Usage

1. Ensure you have poetry installed. Read [here](https://python-poetry.org/docs/#ci-recommendations) for instructions how to install if not.

2. Navigate to the root directory of this project and run `poetry install`.

3. Put your travel dates in the accompanying `travels.csv` file. The fields in the file are as follows:

   - _departure_ (string, dd-mm-yyyy) - The date on which you exit the UK.
   - _arrival_ (string, dd-mm-yyyy) - The date on which you re-enter the UK.
   - _work_ (boolean) - Whether the trip is work related.
   - _leaves_ (int) - The number of annual leaves used in your travel.

4. Run `poetry run python residency_calculator.py`.
