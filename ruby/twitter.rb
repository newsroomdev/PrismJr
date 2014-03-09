require twitter

client = Twitter::Streaming::Client.new do |config|
  config.consumer_key        = ENV["TW_CONSUMER_KEY"]
  config.consumer_secret     = ENV["TW_CONSUMER_SECRET"]
  config.access_token        = ENV["ACCESS_TOKEN"]
  config.access_token_secret = ENV["ACCESS_SECRET"]
end