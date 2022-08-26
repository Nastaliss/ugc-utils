import axios from 'axios'
import React, { useEffect, useState } from 'react'
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'


export const Map = () => {

    const [_isLoaded, setIsLoaded] = useState(false);
    const [theatres, setTheatres] = useState([])

    useEffect(() => {
        console.log("here")
        axios.get(`${process.env.REACT_APP_API_URL}/theatres`).then((r) => {
            console.log(r);
            setTheatres(r.data);
            setIsLoaded(true);
        }, (e) => {
            setIsLoaded(false);
            console.log(e);

        });
}, [] )
  return (
    <MapContainer center={[
        48.859801, 2.346648]} zoom={13} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        { theatres.map((theatre, index) => (
            <Marker position={[theatre["lat"], theatre["lon"]]} key={index}>
                <Popup>
                {theatre["name"]}
                </Popup>
            </Marker>
        ))}

      </MapContainer>
  )
}
