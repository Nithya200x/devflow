import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FiActivity } from 'react-icons/fi';
import { StatCard } from '../components/Cards/StatCard';

describe('StatCard', () => {
  it('renders label, value, and icon', () => {
    render(<StatCard icon={FiActivity} label="Requests" value="42" color="blue" />);
    expect(screen.getByText('Requests')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });
});
