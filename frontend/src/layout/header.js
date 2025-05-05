import React from 'react'
import Link from 'next/link'

export default function Header({handleOnClick, ActiveIndex}) {
    
    return (
        <>
            {/* HEADER */}
            <div className="cavani_tm_header">
                <div className="logo">
                    <a href="#"><img src="img/logo/dark.png" alt="" /></a>
                </div>
                <div className="menu">
                    <ul className="transition_link">
                        <li onClick={() => handleOnClick(0)}><a className={ActiveIndex === 0 ? "active" : ""}>Home</a></li>
                        <li onClick={() => handleOnClick(1)}><a className={ActiveIndex === 1 ? "active" : ""}>About</a></li>
                        <li><Link href="/molecules"><a>Molecules</a></Link></li>
                        <li><Link href="/genomics"><a>Genomics</a></Link></li>
                        <li><Link href="/mass-spec"><a>Mass Spec</a></Link></li>
                        <li onClick={() => handleOnClick(4)}><a className={ActiveIndex === 4 ? "active" : ""}>Evidence</a></li>
                        <li onClick={() => handleOnClick(5)}><a className={ActiveIndex === 5 ? "active" : ""}>News</a></li>
                        <li onClick={() => handleOnClick(6)}><a className={ActiveIndex === 6 ? "active" : ""}>Contact</a></li>
                    </ul>
                    {/* <span className="ccc" /> */}
                </div>
            </div>
            {/* /HEADER */}

        </>
    )
}
