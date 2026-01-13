import StrategyPanel from './features/Strategy/StrategyPanel';
import Assets from './features/Assets/Assets';
import History from './features/History/History';
import OpenOrders from './features/OpenOrders/OpenOrders';
import Dashboard from './features/pages/Dashboard'; 

export default function App() {
  return (
    <div>
      <StrategyPanel />
      <Assets/>
      <History/>
      <OpenOrders/>
      <Dashboard/>
    </div>
  );
};