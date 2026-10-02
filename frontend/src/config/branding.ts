/**
 * AI DataLab — Centralized Branding Configuration
 * Easily customize application name, company, version, and branding assets.
 */

export interface BrandingConfig {
  productName: string
  productTagline: string
  version: string
  companyName: string
  supportEmail: string
  docsUrl: string
  githubUrl: string
  copyrightText: string
  allowCustomTheme: boolean
  defaultTheme: 'dark' | 'light' | 'system'
}

export const branding: BrandingConfig = {
  productName: 'AI DataLab',
  productTagline: 'Agentic Autonomous Data Science, AutoML & MLOps Platform',
  version: '2.4.0-enterprise',
  companyName: 'DataWise AI Systems Inc.',
  supportEmail: 'support@datalab.ai',
  docsUrl: 'https://docs.datalab.ai',
  githubUrl: 'https://github.com/datalab-ai/datalab',
  copyrightText: '© 2026 AI DataLab Inc. All rights reserved. Enterprise Edition.',
  allowCustomTheme: true,
  defaultTheme: 'dark',
}

export const BRANDING = {
  ...branding,
  shortName: 'DL',
  tagline: branding.productTagline,
}

export default branding
