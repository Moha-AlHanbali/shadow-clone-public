# Python version
FROM python:3

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Copy project
COPY . /code/

#  Run the program
CMD [ "python3", "-m" , "gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]
