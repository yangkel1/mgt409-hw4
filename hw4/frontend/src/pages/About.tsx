import { Bulldog } from '../components/Bulldog'

export default function About() {
  return (
    <div className="container section narrow">
      <div className="about-hero">
        <Bulldog size={110} mood="wink" />
        <span className="pennant-big">
          <span>YALE</span>
        </span>
      </div>
      <p className="eyebrow varsity">About us</p>
      <h1>A New Haven shop for Bulldog fans everywhere</h1>
      <p>
        Campus Customs runs Yale Bulldog Blue, a store dedicated to officially licensed Yale apparel. Our store sits on
        Broadway in New Haven, a short walk from Old Campus, close to the people who wear our gear: students heading to class, alumni back for reunions, and families cheering at The Game.
      </p>
      <p>
        Our shelves cover the classics and the new: big block-letter hoodies, left-chest crewnecks for every
        varsity team, residential college and graduate school designs, and limited runs for rivalry weekends.
        Whatever corner of Yale you belong to, we want you to find something that feels like yours.
      </p>

      <h2>What we stand for</h2>
      <ul className="about-list">
        <li>
          <strong>Real licensing.</strong> Everything we sell is officially licensed Yale merchandise.
        </li>
        <li>
          <strong>A local shop.</strong> We are part of the New Haven community, not a faraway warehouse.
        </li>
        <li>
          <strong>Straight answers.</strong> Prices and stock on this site come straight from our inventory, so
          what you see is what we have.
        </li>
      </ul>

      <h2>Visit or contact us</h2>
      <p>
        Stop by at 57 Broadway, New Haven, CT 06511, or email orderdept@campuscustoms.com with order questions.
        Unworn items with original tags can be returned within 30 days of shipping. Custom and final-sale pieces
        can't be returned.
      </p>
    </div>
  )
}
