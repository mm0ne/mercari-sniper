# Use the official Python image as the base image
FROM gorialis/discord.py:bullseye-master-minimal


# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    unzip

# Add Google Chrome repository key
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -

# Add Google Chrome repository
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Update package sources and install Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# Download and install ChromeDriver
RUN wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver.zip
RUN mv ./chromedriver-linux64/chromedriver /usr/local/bin
RUN chmod +x /usr/local/bin/chromedriver

# Set the working directory within the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt

# Run your Python script
CMD ["python", "bot.py"]
