const https = require('https');
const fs = require('fs');

const url = 'https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson';
const dest = 'frontend/public/india_districts.geojson';

const file = fs.createWriteStream(dest);
https.get(url, (response) => {
  if (response.statusCode === 200) {
    response.pipe(file);
    file.on('finish', () => {
      file.close();
      console.log('Download completed.');
    });
  } else {
    console.error('Failed to download: ' + response.statusCode);
  }
}).on('error', (err) => {
  console.error('Error: ' + err.message);
});
