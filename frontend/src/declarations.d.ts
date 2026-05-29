declare module '@mapbox/togeojson' {
  export function kml(doc: Document): GeoJSON.FeatureCollection
}

declare module 'threebox-plugin' {
  import type { Map } from 'mapbox-gl'
  export class Threebox {
    constructor(map: Map, gl: WebGLRenderingContext, opts?: { defaultLights?: boolean })
    line(opts: { geometry: number[][]; color?: number; width?: number; opacity?: number }): any
    label(opts: { htmlElement: string; alwaysVisible?: boolean }): any
    add(obj: any, layerId?: string): void
    remove(obj: any): void
    clear(): void
    update(): void
  }
}
