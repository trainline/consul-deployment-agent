#!/usr/bin/env ruby

require 'uri'
require 'digest/md5'

artifactory_base_url = ENV['artifactory_base_url']
artifactory_user = ENV['artifactory_user']
artifactory_password = ENV['artifactory_password']

if ARGV.length < 2
  puts "Usage: #{File.basename(__FILE__)} <base_url_path> <file1> [file2] [file3] ..."
  puts
  puts "E.g. #{File.basename(__FILE__)} yum-internal-master/OEL/7/x86_64 *.rpm"
  exit 1
end

url_path = ARGV[0]

abort "Don't include the initial 'artifactory' in the url sub-path, just start with the repo & go down as deep as you need" if url_path =~ /^\/*artifactory\//
abort "Don't include a slash at the start of the base-artifactory-path" if url_path =~ /^\//
abort "Don't include a slash at the end of the base-artifactory-path" if url_path =~ /\/$/
abort "Provide a artifactory_user environment variable" unless artifactory_user && !artifactory_user.empty?
abort "Provide a artifactory_password environment variable" unless artifactory_password && !artifactory_password.empty?

ARGV.shift

def upload_to_artifactory(filename, url, user, password)
  digMD5 = Digest::MD5.new
  digSHA1 = Digest::SHA1.new
  File.open(filename, 'rb') do |io|
    buf = ""
    while io.read(65536, buf) do
      digMD5.update(buf)
      digSHA1.update(buf)
    end
  end
  system("curl -v -X PUT -i -T #{filename} -u \"#{user}:#{password}\" -H\"X-Checksum-Md5:#{digMD5}\" -H\"X-Checksum-Sha1:#{digSHA1}\" #{url}")
end

ARGV.each do |file|
  puts "Uploading #{file} to ..."
  file_basename = File.basename(file)
  uri = URI::join(artifactory_base_url, url_path+'/', file_basename)
  url = uri.to_s
  puts url
  upload_to_artifactory(file, url, artifactory_user, artifactory_password)
end
